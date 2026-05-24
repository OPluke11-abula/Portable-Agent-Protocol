"""Tests for PAP Security Enhancements (Task 3-02).

Validates prompt variable escaping, path traversal prevention, memory key
validation, and granular skill authorization level checks.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agent_runtime import (
    AgentEngine,
    PromptComposer,
    SafePromptString,
    validate_prompt_string,
    escape_prompt_value,
)
from agent_runtime.memory import create_memory_backend
from agent_runtime.router import Router, validate_skill_id


# ===========================================================================
# 1. Prompt Injection & Escaping Tests
# ===========================================================================

def test_prompt_composer_variable_escaping() -> None:
    # Test XML tag escaping
    assert escape_prompt_value("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    
    # Test curly braces remain literal
    assert escape_prompt_value("user {input} value") == "user {input} value"

    # Test non-string fallback
    assert escape_prompt_value(123) == "123"


def test_composer_build_escapes_system_variables(tmp_path: Path) -> None:
    prompts_file = tmp_path / "prompts.md"
    prompts_file.write_text("""\
# Prompts catalog
## system_prompt
```text
You are {agent_name}. Instructions: {instructions}
```
""", encoding="utf-8")

    engine = MagicMock()
    engine.config_path = tmp_path / ".agent" / "agent.md"
    engine.layout = {
        "entrypoints": {"prompts": prompts_file},
        "directories": {"prompts": tmp_path / "prompts"},
    }

    composer = PromptComposer(engine)
    
    # Injected raw system variable should be escaped
    res = composer.build(
        "system_prompt",
        {
            "agent_name": "<HackBot>",
            "instructions": "Use {brackets} and tags <br> safely."
        }
    )
    assert "&lt;HackBot&gt;" in res
    assert "Use {brackets}" in res
    assert "tags &lt;br&gt; safely." in res


# ===========================================================================
# 2. Path Traversal Tests (skill_id Sanitization)
# ===========================================================================

def test_router_skill_id_validation() -> None:
    # Allowed formats
    validate_skill_id("valid_skill")
    validate_skill_id("valid-skill-123")

    # Path traversal attempts
    with pytest.raises(ValueError, match="Invalid skill_id format"):
        validate_skill_id("../traversal")
    with pytest.raises(ValueError, match="Invalid skill_id format"):
        validate_skill_id("..\\traversal")
    with pytest.raises(ValueError, match="Invalid skill_id format"):
        validate_skill_id("/absolute/path")
    with pytest.raises(ValueError, match="Invalid skill_id format"):
        validate_skill_id("invalid.char")
    with pytest.raises(ValueError, match="Invalid skill_id format"):
        validate_skill_id("space in name")

    # Type/empty checks
    with pytest.raises(TypeError, match="must be a string"):
        validate_skill_id(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_skill_id("")


# ===========================================================================
# 3. Memory Key Validation Tests
# ===========================================================================

@pytest.mark.parametrize("backend_name", ["in_memory", "json", "sqlite"])
def test_memory_key_validation(backend_name: str, tmp_path: Path) -> None:
    db_path = tmp_path / "test_mem"
    if backend_name == "sqlite":
        db_path = tmp_path / "test_mem.db"
    
    backend = create_memory_backend(backend_name, path=db_path)

    # Clean keys should pass
    backend.write("clean_key", "value")
    assert backend.read("clean_key") == "value"
    assert backend.delete("clean_key") is True

    # Oversized key (> 256 chars)
    oversized = "a" * 257
    with pytest.raises(ValueError, match="exceeds maximum length"):
        backend.write(oversized, "value")
    with pytest.raises(ValueError, match="exceeds maximum length"):
        backend.read(oversized)
    with pytest.raises(ValueError, match="exceeds maximum length"):
        backend.delete(oversized)

    # Directory traversal keys
    with pytest.raises(ValueError, match="cannot contain path separators"):
        backend.write("../bad_key", "value")
    with pytest.raises(ValueError, match="cannot contain path separators"):
        backend.read("folder/key")

    # Null bytes
    with pytest.raises(ValueError, match="cannot contain null bytes"):
        backend.write("bad\x00key", "value")


# ===========================================================================
# 4. Granular Skill Authorization Level Tests
# ===========================================================================

def _write_secure_onboarding_workspace(tmp_path: Path, auth_level: str, skill_auth: str) -> Path:
    agent_dir = tmp_path / ".agent"
    skills_dir = agent_dir / "skills"
    memory_dir = agent_dir / "memory"
    workflows_dir = agent_dir / "workflows"
    knowledge_dir = agent_dir / "knowledge_base"
    for directory in (skills_dir, memory_dir, workflows_dir, knowledge_dir):
        directory.mkdir(parents=True, exist_ok=True)

    (agent_dir / "skills.md").write_text("# Skills\n", encoding="utf-8")
    (agent_dir / "handoff_guide.md").write_text("# Handoff\n", encoding="utf-8")
    (tmp_path / "agent_tasks.md").write_text("# Tasks\n", encoding="utf-8")
    
    (skills_dir / "test_tool.md").write_text(f"""---
id: "test_tool"
name: "test_tool"
description: "A test tool"
version: "1.0.0"
authorization_level: "{skill_auth}"
inputs: {{}}
outputs: {{}}
safety_notes: []
---
# test_tool
""", encoding="utf-8")

    config_path = agent_dir / "agent.md"
    config_path.write_text(f"""---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: "security_test"
version: "0.1.0"
purpose: "Test skill permissions"
language: "en-US"
authorization_level: "{auth_level}"
use_case_tags: ["test"]
tools:
  - test_tool
protocol:
  root: ".agent/"
  manifest: ".agent/agent.md"
  entrypoints:
    skills: ".agent/skills.md"
    tasks: agent_tasks.md
    handoff: ".agent/handoff_guide.md"
  directories:
    skills: ".agent/skills/"
    workflows: ".agent/workflows/"
    memory: ".agent/memory/"
    knowledge_base: ".agent/knowledge_base/"
memory:
  backend: "in_memory"
---
# Onboarding Agent
""", encoding="utf-8")
    return config_path


def _complete_onboarding(engine: AgentEngine) -> None:
    # Read the sequence to complete onboarding
    engine.read_onboarding_file("skills.md")
    engine.read_onboarding_file("agent_tasks.md")
    engine.read_onboarding_file("handoff_guide.md")
    assert engine.onboarding_status["complete"] is True


def test_engine_skill_call_permission_auto(tmp_path: Path) -> None:
    config_path = _write_secure_onboarding_workspace(tmp_path, "autonomous", "auto")
    engine = AgentEngine(config_path, bypass_onboarding=False)
    _complete_onboarding(engine)
    
    # Mock tool execution
    engine.router.register_tool("test_tool", lambda params: {"result": "success"})

    # Auto permission executes directly without prompting
    res = engine.call_skill("test_tool", {})
    assert res == {"result": "success"}


def test_engine_skill_call_permission_deny(tmp_path: Path) -> None:
    config_path = _write_secure_onboarding_workspace(tmp_path, "interactive-approval", "deny")
    engine = AgentEngine(config_path, bypass_onboarding=False)
    _complete_onboarding(engine)
    
    engine.router.register_tool("test_tool", lambda params: {"result": "success"})

    # Denied permission throws PermissionError
    with pytest.raises(PermissionError, match="blocked by security policy"):
        engine.call_skill("test_tool", {})


def test_engine_skill_call_permission_interactive_approval(tmp_path: Path) -> None:
    # 1. Test case: Rejected by callback
    config_path = _write_secure_onboarding_workspace(tmp_path, "interactive-approval", "interactive-approval")
    
    engine1 = AgentEngine(
        config_path,
        bypass_onboarding=False,
        approval_callback=lambda skill_id, params: False,
    )
    _complete_onboarding(engine1)
    engine1.router.register_tool("test_tool", lambda params: {"result": "success"})
    with pytest.raises(PermissionError, match="rejected by the user"):
        engine1.call_skill("test_tool", {})

    # 2. Test case: Approved by callback
    # Create new temp directory path for isolated sqlite/file memory backend state
    tmp_path2 = tmp_path / "engine2"
    config_path2 = _write_secure_onboarding_workspace(tmp_path2, "interactive-approval", "interactive-approval")
    engine2 = AgentEngine(
        config_path2,
        bypass_onboarding=False,
        approval_callback=lambda skill_id, params: True,
    )
    _complete_onboarding(engine2)
    engine2.router.register_tool("test_tool", lambda params: {"result": "success"})
    assert engine2.call_skill("test_tool", {}) == {"result": "success"}

    # 3. Test case: No callback in non-TTY environment raises PermissionError
    tmp_path3 = tmp_path / "engine3"
    config_path3 = _write_secure_onboarding_workspace(tmp_path3, "interactive-approval", "interactive-approval")
    engine3 = AgentEngine(config_path3, bypass_onboarding=False)
    _complete_onboarding(engine3)
    engine3.router.register_tool("test_tool", lambda params: {"result": "success"})
    with pytest.raises(PermissionError, match="requires interactive approval but no interactive terminal or callback"):
        engine3.call_skill("test_tool", {})

