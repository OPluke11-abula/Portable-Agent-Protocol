"""Edge-case tests for the public PAP engine bootstrap interface."""

from __future__ import annotations

import logging
import textwrap
from pathlib import Path

import pytest
import yaml

from agent_runtime import engine as engine_module
from agent_runtime.engine import AgentEngine, load_agent_config


def _copy_agent_schema(tmp_path: Path) -> None:
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    schema_text = Path("spec/agent-schema.json").read_text(encoding="utf-8")
    (spec_dir / "agent-schema.json").write_text(schema_text, encoding="utf-8")


def _write_workspace(tmp_path: Path, frontmatter: str) -> Path:
    agent_dir = tmp_path / ".agent"
    for child in ("skills", "workflows", "memory", "knowledge_base"):
        (agent_dir / child).mkdir(parents=True, exist_ok=True)

    config_path = agent_dir / "agent.md"
    config_path.write_text(
        f"---\n{textwrap.dedent(frontmatter).strip()}\n---\n# Test Agent\n",
        encoding="utf-8",
    )
    return config_path


def _valid_frontmatter(
    tmp_path: Path,
    *,
    protocol_version: str = "1.0.0",
    min_runtime_version: str = "0.1.0",
) -> str:
    memory_path = (tmp_path / ".agent" / "memory").as_posix()
    return f"""
    protocol_version: "{protocol_version}"
    min_runtime_version: "{min_runtime_version}"
    name: test-agent
    version: "0.1.0"
    purpose: Test PAP engine edge cases.
    language: en-US
    authorization_level: interactive-approval
    use_case_tags: [test]
    tools: []
    protocol:
      root: .agent/
      manifest: .agent/agent.md
      directories:
        skills: .agent/skills/
        workflows: .agent/workflows/
        memory: .agent/memory/
        knowledge_base: .agent/knowledge_base/
    memory:
      backend: in_memory
      path: "{memory_path}"
    """


@pytest.mark.skipif(
    engine_module.jsonschema is None,
    reason="jsonschema package is required for schema rejection behavior",
)
def test_engine_rejects_missing_required_manifest_field(tmp_path: Path) -> None:
    """Schema-backed bootstrapping rejects configs missing required PAP fields."""
    _copy_agent_schema(tmp_path)
    config_path = _write_workspace(
        tmp_path,
        _valid_frontmatter(tmp_path).replace(
            "    purpose: Test PAP engine edge cases.\n", ""
        ),
    )

    with pytest.raises(ValueError, match="purpose"):
        AgentEngine(config_path)


def test_load_agent_config_surfaces_malformed_yaml(tmp_path: Path) -> None:
    """Malformed YAML front matter fails at the config loader boundary."""
    config_path = tmp_path / "agent.md"
    config_path.write_text(
        "---\nname: [unterminated\n---\n# Broken Agent\n",
        encoding="utf-8",
    )

    with pytest.raises(yaml.YAMLError):
        load_agent_config(config_path)


def test_engine_logs_version_mismatch_warnings(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    """Runtime and protocol version mismatches are warnings, not load blockers."""
    _copy_agent_schema(tmp_path)
    config_path = _write_workspace(
        tmp_path,
        _valid_frontmatter(
            tmp_path,
            protocol_version="2.0.0",
            min_runtime_version="9.9.9",
        ),
    )

    with caplog.at_level(logging.WARNING):
        engine = AgentEngine(config_path)

    messages = [record.message for record in caplog.records]
    assert engine.config["protocol_version"] == "2.0.0"
    assert any("requires minimum runtime version 9.9.9" in msg for msg in messages)
    assert any("uses protocol version 2.0.0" in msg for msg in messages)
