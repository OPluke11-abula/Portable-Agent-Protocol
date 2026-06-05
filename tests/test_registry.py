"""Unit tests for public skill registry validation, installation, and publication."""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

from agent_runtime.registry import (
    install_skill,
    publish_skill,
    validate_skill_contract,
    get_registry_url,
)


def _write_valid_contract(path: Path, skill_id: str = "valid_tool") -> None:
    path.write_text(
        textwrap.dedent(
            f"""\
            ---
            id: {skill_id}
            name: {skill_id}
            description: A perfectly valid community tool contract.
            version: 1.2.3
            inputs:
              param1:
                type: string
                description: Parameter one.
                required: true
            outputs:
              result:
                type: object
                description: Result payload.
            safety_notes:
              - Always inspect inputs.
            author: community-member
            ---
            # Skill: {skill_id}
            """
        ),
        encoding="utf-8",
    )


class TestRegistry:
    def test_validate_skill_contract_success(self, tmp_path: Path) -> None:
        """Verify that a compliant skill contract passes validation."""
        path = tmp_path / "valid_tool.md"
        _write_valid_contract(path)
        data = validate_skill_contract(path)
        assert data["id"] == "valid_tool"
        assert data["version"] == "1.2.3"

    def test_validate_skill_contract_failures(self, tmp_path: Path) -> None:
        """Verify that various validation rules raise ValueError for non-compliant contracts."""
        # 1. Missing name/id
        path1 = tmp_path / "invalid1.md"
        path1.write_text(
            textwrap.dedent(
                """\
                ---
                id: invalid_tool
                description: Missing name
                version: 1.0.0
                inputs: {}
                outputs: {}
                safety_notes:
                  - constraint
                ---
                """
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="Schema validation failed|missing 'id' or 'name'"):
            validate_skill_contract(path1)

        # 2. Mismatched id and name
        path2 = tmp_path / "invalid2.md"
        path2.write_text(
            textwrap.dedent(
                """\
                ---
                id: my_tool
                name: other_tool
                description: Mismatched name
                version: 1.0.0
                inputs: {}
                outputs: {}
                safety_notes:
                  - constraint
                ---
                """
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="must be identical to 'name'"):
            validate_skill_contract(path2)

        # 3. Invalid semver
        path3 = tmp_path / "invalid3.md"
        path3.write_text(
            textwrap.dedent(
                """\
                ---
                id: my_tool
                name: my_tool
                description: Bad version
                version: v1.0
                inputs: {}
                outputs: {}
                safety_notes:
                  - constraint
                ---
                """
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="Schema validation failed|not a valid semver pattern"):
            validate_skill_contract(path3)

        # 4. Forbidden vendor term
        path4 = tmp_path / "invalid4.md"
        path4.write_text(
            textwrap.dedent(
                """\
                ---
                id: my_tool
                name: my_tool
                description: Mentions Claude
                version: 1.0.0
                inputs: {}
                outputs: {}
                safety_notes:
                  - constraint
                ---
                This contract is optimized for anthropic models.
                """
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="Forbidden vendor-specific term"):
            validate_skill_contract(path4)

    def test_local_publish_and_install_lifecycle(self, tmp_path: Path) -> None:
        """Verify the publication to registry and subsequent installation back to active workspace."""
        registry_dir = tmp_path / "registry"
        registry_dir.mkdir()
        
        # Initialize registry index
        index_path = registry_dir / "index.json"
        index_path.write_text(json.dumps({"registry_version": "1.0.0", "skills": {}}), encoding="utf-8")

        # Create a valid contract outside the registry
        contrib_path = tmp_path / "my_contrib.md"
        _write_valid_contract(contrib_path, "my_contrib")

        # 1. Publish to the registry
        entry = publish_skill(contrib_path, registry_dir=registry_dir)
        assert entry["id"] == "my_contrib"
        assert entry["version"] == "1.2.3"
        assert entry["path"] == "skills/my_contrib.md"

        # Verify registry files exist
        assert (registry_dir / "skills" / "my_contrib.md").exists()
        index_data = json.loads(index_path.read_text(encoding="utf-8"))
        assert "my_contrib" in index_data["skills"]

        # 2. Install from registry to active skills dir
        active_skills_dir = tmp_path / "active_skills"
        installed_entry = install_skill("my_contrib", skills_dir=active_skills_dir, registry_dir=registry_dir)
        
        assert installed_entry["id"] == "my_contrib"
        assert (active_skills_dir / "my_contrib.md").exists()

        # 3. Attempt to install non-existent skill raises KeyError
        with pytest.raises(KeyError, match="not found in the registry index"):
            install_skill("non_existent", skills_dir=active_skills_dir, registry_dir=registry_dir)

    @patch("urllib.request.urlopen")
    def test_remote_url_installation(self, mock_urlopen: MagicMock, tmp_path: Path) -> None:
        """Verify fetching and installing from a remote static URL registry via mocked urllib request."""
        # Setup mock responses
        mock_index_response = MagicMock()
        mock_index_response.read.return_value = json.dumps({
            "registry_version": "1.0.0",
            "skills": {
                "remote_tool": {
                    "id": "remote_tool",
                    "name": "remote_tool",
                    "version": "1.0.0",
                    "description": "Remote tool description",
                    "author": "remote-author",
                    "path": "skills/remote_tool.md"
                }
            }
        }).encode("utf-8")

        mock_contract_response = MagicMock()
        mock_contract_response.read.return_value = textwrap.dedent(
            """\
            ---
            id: remote_tool
            name: remote_tool
            description: Remote tool contract.
            version: 1.0.0
            inputs:
              q:
                type: string
                description: query.
                required: true
            outputs:
              res:
                type: string
                description: response.
            safety_notes:
              - No constraints.
            author: remote-author
            ---
            # Skill: remote_tool
            """
        ).encode("utf-8")

        # Configure context manager entries
        mock_index_response.__enter__.return_value = mock_index_response
        mock_contract_response.__enter__.return_value = mock_contract_response

        # mock urlopen to return index response first, then contract response
        mock_urlopen.side_effect = [mock_index_response, mock_contract_response]

        # Enable remote URL registry environment variable
        with patch.dict(os.environ, {"PAP_REGISTRY_URL": "https://registry.example.com"}):
            assert get_registry_url() == "https://registry.example.com"

            active_skills_dir = tmp_path / "active_skills"
            entry = install_skill("remote_tool", skills_dir=active_skills_dir)

            assert entry["id"] == "remote_tool"
            assert (active_skills_dir / "remote_tool.md").exists()
            assert "Remote tool contract" in (active_skills_dir / "remote_tool.md").read_text(encoding="utf-8")
