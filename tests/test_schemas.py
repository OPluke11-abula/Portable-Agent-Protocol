"""Tests to enforce that all .md files in the .agent/ workspace conform to their JSON schemas."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

try:
    import jsonschema
except ImportError:
    jsonschema = None

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _load_frontmatter(path: Path) -> dict[str, Any]:
    """Parse YAML front matter from a markdown file."""
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"No YAML front-matter found in {path}")
    return yaml.safe_load(match.group(1)) or {}


@pytest.mark.skipif(jsonschema is None, reason="jsonschema package not installed")
class TestProtocolSchemas:
    def test_agent_manifest_schema(self) -> None:
        """Validate .agent/agent.md against spec/agent-schema.json."""
        manifest_path = Path(".agent/agent.md")
        schema_path = Path("spec/agent-schema.json")
        
        assert manifest_path.exists()
        assert schema_path.exists()
        
        manifest_config = _load_frontmatter(manifest_path)
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        
        jsonschema.validate(instance=manifest_config, schema=schema)

    def test_skill_contracts_schema(self) -> None:
        """Validate all skills in .agent/skills/*.md against spec/skill-contract.schema.json."""
        skills_dir = Path(".agent/skills")
        schema_path = Path("spec/skill-contract.schema.json")
        
        assert skills_dir.exists()
        assert schema_path.exists()
        
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        
        skill_files = list(skills_dir.glob("*.md"))
        assert len(skill_files) > 0, "No skill files found"
        
        for path in skill_files:
            if path.name in ("_template.md", "__init__.md"):
                continue
            
            try:
                skill_config = _load_frontmatter(path)
                jsonschema.validate(instance=skill_config, schema=schema)
            except Exception as e:
                pytest.fail(f"Skill contract {path.name} failed schema validation: {e}")

    def test_workflow_contracts_schema(self) -> None:
        """Validate all workflows in .agent/workflows/*.md against spec/workflow.schema.json."""
        workflows_dir = Path(".agent/workflows")
        schema_path = Path("spec/workflow.schema.json")
        
        assert workflows_dir.exists()
        assert schema_path.exists()
        
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        
        workflow_files = list(workflows_dir.glob("*.md"))
        assert len(workflow_files) > 0, "No workflow files found"
        
        for path in workflow_files:
            if path.name in ("__init__.md",):
                continue
            
            try:
                workflow_config = _load_frontmatter(path)
                jsonschema.validate(instance=workflow_config, schema=schema)
            except Exception as e:
                pytest.fail(f"Workflow contract {path.name} failed schema validation: {e}")
