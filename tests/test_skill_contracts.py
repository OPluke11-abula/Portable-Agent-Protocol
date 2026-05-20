"""Comprehensive contract tests for Portable Agent Protocol skills."""

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
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# List of vendor-specific terms to forbid in skill contracts
_FORBIDDEN_VENDOR_TERMS = [
    "anthropic",
    "claude",
    "openai",
    "gpt-4",
    "gpt-3",
    "gemini",
    "vertex",
    "langchain",
]


def _load_frontmatter(path: Path) -> dict[str, Any]:
    """Parse YAML front matter from a markdown file."""
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"No YAML front-matter found in {path}")
    return yaml.safe_load(match.group(1)) or {}


def get_skill_contracts() -> list[Path]:
    """Get paths to all active skill contract files."""
    skills_dir = Path(".agent/skills")
    if not skills_dir.exists():
        return []
    return [
        p
        for p in skills_dir.glob("*.md")
        if p.name not in ("_template.md", "__init__.md")
    ]


@pytest.mark.skipif(jsonschema is None, reason="jsonschema package not installed")
class TestSkillContracts:
    def test_schema_conformance(self) -> None:
        """Validate all active skills against spec/skill-contract.schema.json."""
        schema_path = Path("spec/skill-contract.schema.json")
        assert schema_path.exists(), "Schema file spec/skill-contract.schema.json does not exist"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        contracts = get_skill_contracts()
        assert len(contracts) > 0, "No active skill contracts found in .agent/skills/"

        for path in contracts:
            try:
                skill_config = _load_frontmatter(path)
                jsonschema.validate(instance=skill_config, schema=schema)
            except Exception as e:
                pytest.fail(f"Skill contract {path.name} failed JSON Schema validation: {e}")

    def test_contract_rules(self) -> None:
        """Assert strict custom business rules for skill contracts."""
        contracts = get_skill_contracts()
        for path in contracts:
            skill_config = _load_frontmatter(path)

            # Rule 1: id and name must be present and identical
            assert "id" in skill_config, f"{path.name} is missing 'id'"
            assert "name" in skill_config, f"{path.name} is missing 'name'"
            assert skill_config["id"] == skill_config["name"], (
                f"{path.name}: 'id' ({skill_config['id']}) must be identical to 'name' ({skill_config['name']})"
            )

            # Rule 2: version must match semver pattern
            assert "version" in skill_config, f"{path.name} is missing 'version'"
            assert _SEMVER_RE.match(skill_config["version"]), (
                f"{path.name}: version '{skill_config['version']}' is not a valid semver"
            )

            # Rule 3: inputs structure and description validation
            assert "inputs" in skill_config, f"{path.name} is missing 'inputs'"
            inputs = skill_config["inputs"]
            assert isinstance(inputs, dict), f"{path.name}: 'inputs' must be an object"
            for param_name, param_info in inputs.items():
                assert "type" in param_info, f"{path.name}: input '{param_name}' is missing 'type'"
                assert "description" in param_info, f"{path.name}: input '{param_name}' is missing 'description'"
                assert isinstance(param_info["type"], str), f"{path.name}: input '{param_name}' type must be string"
                assert isinstance(param_info["description"], str), f"{path.name}: input '{param_name}' description must be string"

            # Rule 4: outputs structure validation
            assert "outputs" in skill_config, f"{path.name} is missing 'outputs'"
            outputs = skill_config["outputs"]
            assert isinstance(outputs, dict), f"{path.name}: 'outputs' must be an object"
            for output_name, output_info in outputs.items():
                assert "type" in output_info, f"{path.name}: output '{output_name}' is missing 'type'"
                assert "description" in output_info, f"{path.name}: output '{output_name}' is missing 'description'"
                assert isinstance(output_info["type"], str), f"{path.name}: output '{output_name}' type must be string"
                assert isinstance(output_info["description"], str), f"{path.name}: output '{output_name}' description must be string"

            # Rule 5: safety_notes validation
            assert "safety_notes" in skill_config, f"{path.name} is missing 'safety_notes'"
            safety_notes = skill_config["safety_notes"]
            assert isinstance(safety_notes, list), f"{path.name}: 'safety_notes' must be a list"
            assert len(safety_notes) > 0, f"{path.name}: 'safety_notes' must contain at least one constraint"
            for note in safety_notes:
                assert isinstance(note, str), f"{path.name}: safety note '{note}' must be a string"

    def test_vendor_anonymization(self) -> None:
        """Verify that no forbidden vendor-specific terms exist in active skill contracts."""
        contracts = get_skill_contracts()
        for path in contracts:
            content = path.read_text(encoding="utf-8").lower()
            for term in _FORBIDDEN_VENDOR_TERMS:
                assert term not in content, (
                    f"Forbidden vendor-specific term '{term}' found in skill contract {path.name}"
                )
