"""Tests for strict LAS onboarding enforcement in AgentEngine."""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import pytest

from agent_runtime.engine import AgentEngine


def _write_strict_workspace(tmp_path: Path) -> Path:
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
    (skills_dir / "fake_tool.md").write_text(
        textwrap.dedent(
            """\
            ---
            id: fake_tool
            name: fake_tool
            description: Test tool for onboarding enforcement.
            version: 1.0.0
            inputs:
              text:
                type: string
                required: true
            outputs:
              ok:
                type: boolean
            ---
            # fake_tool
            """
        ),
        encoding="utf-8",
    )

    config_path = agent_dir / "agent.md"
    config_path.write_text(
        textwrap.dedent(
            """\
            ---
            protocol_version: "1.0.0"
            min_runtime_version: "0.1.0"
            name: onboarding-agent
            version: "0.1.0"
            purpose: Verify strict onboarding.
            language: en-US
            authorization_level: interactive-approval
            use_case_tags: [test]
            tools:
              - fake_tool
            protocol:
              root: .agent/
              manifest: .agent/agent.md
              entrypoints:
                skills: .agent/skills.md
                tasks: agent_tasks.md
                handoff: .agent/handoff_guide.md
              directories:
                skills: .agent/skills/
                workflows: .agent/workflows/
                memory: .agent/memory/
                knowledge_base: .agent/knowledge_base/
            memory:
              backend: in_memory
            ---
            # Onboarding Agent
            """
        ),
        encoding="utf-8",
    )
    return config_path


def _register_fake_tool(engine: AgentEngine) -> None:
    def fake_tool(params: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "text": params["text"]}

    engine.router.register_tool("fake_tool", fake_tool)


def test_tool_execution_requires_complete_ordered_onboarding(tmp_path: Path) -> None:
    config_path = _write_strict_workspace(tmp_path)
    engine = AgentEngine(config_path)
    _register_fake_tool(engine)

    assert engine.onboarding_status["read"] == ["agent.md"]
    assert engine.onboarding_status["next"] == "skills.md"

    with pytest.raises(PermissionError, match="Onboarding sequence incomplete"):
        engine.run("fake_tool", {"text": "blocked"})

    assert "Skills" in engine.read_onboarding_file("skills.md")
    assert "Tasks" in engine.read_onboarding_file("agent_tasks.md")
    assert "Handoff" in engine.read_onboarding_file("handoff_guide.md")

    assert engine.onboarding_status["complete"] is True
    assert engine.run("fake_tool", {"text": "allowed"}) == {
        "ok": True,
        "text": "allowed",
    }


def test_onboarding_rejects_out_of_order_reads(tmp_path: Path) -> None:
    config_path = _write_strict_workspace(tmp_path)
    engine = AgentEngine(config_path)

    with pytest.raises(PermissionError, match="Expected skills.md, got agent_tasks.md"):
        engine.read_onboarding_file("agent_tasks.md")

    assert engine.onboarding_status["read"] == ["agent.md"]
    assert engine.onboarding_status["next"] == "skills.md"


def test_engine_owned_router_checks_onboarding_before_direct_dispatch(
    tmp_path: Path,
) -> None:
    config_path = _write_strict_workspace(tmp_path)
    engine = AgentEngine(config_path)
    _register_fake_tool(engine)

    with pytest.raises(PermissionError, match="Onboarding sequence incomplete"):
        engine.router.route("fake_tool", {"text": "blocked"})


def test_onboarding_bypass_allows_trusted_host_bootstrap(tmp_path: Path) -> None:
    config_path = _write_strict_workspace(tmp_path)
    engine = AgentEngine(config_path, bypass_onboarding=True)
    _register_fake_tool(engine)

    assert engine.onboarding_status["bypass"] is True
    assert engine.onboarding_status["complete"] is True
    assert engine.run("fake_tool", {"text": "bootstrap"}) == {
        "ok": True,
        "text": "bootstrap",
    }


def test_onboarding_env_bypass_allows_trusted_host_bootstrap(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PAP_BYPASS_ONBOARDING", "true")
    config_path = _write_strict_workspace(tmp_path)
    engine = AgentEngine(config_path)
    _register_fake_tool(engine)

    assert engine.onboarding_status["bypass"] is True
    assert engine.run("fake_tool", {"text": "env"}) == {
        "ok": True,
        "text": "env",
    }
