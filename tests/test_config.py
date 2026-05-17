"""Tests for loading the agent config from .agent/agent.md."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from agent_runtime.engine import load_agent_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_agent_md(tmp_path: Path, frontmatter: str, body: str = "# body") -> Path:
    """Write a minimal agent.md with the given YAML frontmatter."""
    content = f"---\n{textwrap.dedent(frontmatter).strip()}\n---\n{body}\n"
    p = tmp_path / "agent.md"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLoadAgentConfig:
    def test_loads_name_and_version(self, tmp_path: Path) -> None:
        path = _write_agent_md(
            tmp_path,
            """
            name: test-agent
            version: "1.2.3"
            """,
        )
        config = load_agent_config(path)
        assert config["name"] == "test-agent"
        assert config["version"] == "1.2.3"

    def test_loads_tools_list(self, tmp_path: Path) -> None:
        path = _write_agent_md(
            tmp_path,
            """
            name: test-agent
            version: "0.1.0"
            tools:
              - search_web
              - query_db
            """,
        )
        config = load_agent_config(path)
        assert config["tools"] == ["search_web", "query_db"]

    def test_raises_if_file_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "no_such_file.md"
        with pytest.raises(FileNotFoundError):
            load_agent_config(missing)

    def test_raises_if_no_frontmatter(self, tmp_path: Path) -> None:
        p = tmp_path / "agent.md"
        p.write_text("# Just a markdown file, no front-matter\n")
        with pytest.raises(ValueError, match="front-matter"):
            load_agent_config(p)

    def test_real_agent_md(self) -> None:
        """The actual .agent/agent.md in the repo must parse cleanly."""
        config = load_agent_config(".agent/agent.md")
        assert config.get("name"), "name must be non-empty"
        assert config.get("version"), "version must be non-empty"
        assert isinstance(config.get("tools"), list), "tools must be a list"
        assert len(config["tools"]) > 0, "tools list must not be empty"
