"""Unit tests for the Strict Schema Validation layer including Router exact type checks and Engine bootstrap validation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from agent_runtime.engine import AgentEngine
from agent_runtime.lint import WorkspaceLinter
from agent_runtime.router import Router


def test_router_strict_type_enforcement():
    """Verifies that Router.validate_call rejects wildcards and loose types, and accepts exact types."""
    # Define a clean contract dict
    contract = {
        "id": "my_skill",
        "name": "my_skill",
        "description": "test skill",
        "version": "1.0.0",
        "inputs": {
            "query": {
                "type": "string",
                "description": "The search query",
                "required": True
            },
            "age": {
                "type": "integer",
                "description": "Age",
                "required": False
            }
        },
        "outputs": {
            "result": {
                "type": "string",
                "description": "Output string"
            }
        },
        "safety_notes": []
    }

    # Initialize router and register handler
    router = Router()
    router._registry["my_skill"] = lambda p: {"result": "ok"}
    
    # Inject mock _load_contract function
    router._load_contract = lambda sid: contract if sid == "my_skill" else None

    # Valid parameters pass validation
    router.validate_call("my_skill", {"query": "test", "age": 25})

    # Type mismatch raises ValueError
    with pytest.raises(ValueError, match="has invalid type"):
        router.validate_call("my_skill", {"query": 123})

    # Modify contract to include a loose type ("any")
    contract["inputs"]["query"]["type"] = "any"
    with pytest.raises(ValueError, match="must declare a strict exact JSON type"):
        router.validate_call("my_skill", {"query": "test"})

    # Modify contract to have missing type
    contract["inputs"]["query"]["type"] = None
    with pytest.raises(ValueError, match="must declare a strict exact JSON type"):
        router.validate_call("my_skill", {"query": "test"})


def test_linter_strict_type_checks():
    """Verifies that WorkspaceLinter flags loose parameter types in skill contracts."""
    test_skill_content = """---
id: "test_linter_skill"
name: "test_linter_skill"
description: "A test linter skill."
version: "1.0.0"
inputs:
  bad_param:
    type: "any"
    description: "loose parameter type"
    required: true
outputs:
  result:
    type: "string"
    description: "result"
safety_notes: []
---
# test_linter_skill
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        agent_dir = tmp_path / ".agent"
        agent_dir.mkdir()
        
        # Scaffold basic agent manifest
        manifest_content = """---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: "test-linter"
version: "0.1.0"
purpose: "test"
language: "en-US"
authorization_level: "autonomous"
use_case_tags: ["test"]
tools: ["test_linter_skill"]
protocol:
  root: ".agent/"
  manifest: ".agent/agent.md"
  directories:
    skills: ".agent/skills/"
    workflows: ".agent/workflows/"
memory:
  backend: "local"
  path: ".agent/memory/"
---
# Agent
"""
        (agent_dir / "agent.md").write_text(manifest_content, encoding="utf-8")
        
        skills_dir = agent_dir / "skills"
        skills_dir.mkdir()
        (skills_dir / "test_linter_skill.md").write_text(test_skill_content, encoding="utf-8")
        
        # Scaffold spec folder for schema checks
        project_root = Path.cwd()
        spec_dir = tmp_path / "spec"
        spec_dir.mkdir()
        
        # Copy schemas
        for schema_file in ("agent-schema.json", "skill-contract.schema.json"):
            src = project_root / "spec" / schema_file
            if src.exists():
                (spec_dir / schema_file).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

        linter = WorkspaceLinter(config_path=agent_dir / "agent.md")
        issues = linter.run_all_checks()
        
        # Linter should find the loose type issue
        bad_param_issues = [
            iss for iss in issues
            if "must declare a strict exact JSON type" in iss.message
        ]
        assert len(bad_param_issues) == 1
        assert bad_param_issues[0].severity == "error"
        assert "bad_param" in bad_param_issues[0].message


def test_engine_bootstrap_cycle_and_reference_validation():
    """Verifies that AgentEngine bootstrap fails when a workflow contains a circular dependency or bad references."""
    
    # Workflow with a cycle: step1 depends on step2, step2 depends on step1
    cyclic_workflow_content = """---
name: "cyclic_workflow"
steps:
  - id: "step1"
    tool: "search_web"
    depends_on: ["step2"]
    params:
      query: "hello"
  - id: "step2"
    tool: "search_web"
    depends_on: ["step1"]
    params:
      query: "world"
---
# Cyclic
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        agent_dir = tmp_path / ".agent"
        agent_dir.mkdir()
        
        manifest_content = """---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: "test-engine"
version: "0.1.0"
purpose: "test"
language: "en-US"
authorization_level: "autonomous"
use_case_tags: ["test"]
tools: []
protocol:
  root: ".agent/"
  manifest: ".agent/agent.md"
  directories:
    skills: ".agent/skills/"
    workflows: ".agent/workflows/"
memory:
  backend: "local"
  path: ".agent/memory/"
---
# Agent
"""
        (agent_dir / "agent.md").write_text(manifest_content, encoding="utf-8")
        
        workflows_dir = agent_dir / "workflows"
        workflows_dir.mkdir()
        (workflows_dir / "cyclic_workflow.md").write_text(cyclic_workflow_content, encoding="utf-8")
        
        skills_dir = agent_dir / "skills"
        skills_dir.mkdir()
        (agent_dir / "memory").mkdir()
        
        # Copy schemas
        project_root = Path.cwd()
        spec_dir = tmp_path / "spec"
        spec_dir.mkdir()
        for schema_file in ("agent-schema.json", "workflow.schema.json"):
            src = project_root / "spec" / schema_file
            if src.exists():
                (spec_dir / schema_file).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

        # Startup engine should raise a ValueError due to circular dependency check at bootstrap
        with pytest.raises(ValueError, match="circular dependency detected"):
            AgentEngine(config_path=agent_dir / "agent.md", enforce_onboarding=False)
