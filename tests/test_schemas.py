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

    def test_knowledge_entries_schema(self) -> None:
        """Validate all knowledge entries in .agent/knowledge_base/*.md against spec/knowledge.schema.json."""
        kb_dir = Path(".agent/knowledge_base")
        schema_path = Path("spec/knowledge.schema.json")

        assert kb_dir.exists()
        assert schema_path.exists()

        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        kb_files = [
            p for p in kb_dir.glob("*.md")
            if p.name not in ("__init__.md",)
        ]
        assert len(kb_files) > 0, "No knowledge base files found"

        for path in kb_files:
            try:
                kb_config = _load_frontmatter(path)
                jsonschema.validate(instance=kb_config, schema=schema)
            except Exception as e:
                pytest.fail(f"Knowledge entry {path.name} failed schema validation: {e}")

    def test_prompt_contracts_schema(self) -> None:
        """Validate all prompt contracts in .agent/prompts/*.md against spec/prompt.schema.json."""
        prompts_dir = Path(".agent/prompts")
        schema_path = Path("spec/prompt.schema.json")

        assert prompts_dir.exists()
        assert schema_path.exists()

        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        prompt_files = [
            p for p in prompts_dir.glob("*.md")
            if p.name not in ("__init__.md",)
        ]
        assert len(prompt_files) > 0, "No prompt files found"

        for path in prompt_files:
            text = path.read_text(encoding="utf-8")
            match = _FRONTMATTER_RE.match(text)
            if not match:
                pytest.fail(f"Prompt file {path.name} is missing front matter")

            try:
                metadata = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError as exc:
                pytest.fail(f"Prompt file {path.name} has invalid YAML front matter: {exc}")

            body = text[match.end():].strip()

            prompt_dict = {
                "id": metadata.get("id", path.stem),
                "version": metadata.get("version", "1.0.0"),
                "usage": metadata.get("usage", ""),
                "variables": metadata.get("variables", []),
                "template": body,
            }

            try:
                jsonschema.validate(instance=prompt_dict, schema=schema)
            except Exception as e:
                pytest.fail(f"Prompt contract {path.name} failed schema validation: {e}")


