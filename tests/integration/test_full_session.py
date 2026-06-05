"""Full-session integration coverage for the PAP runtime surface."""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

from agent_runtime.engine import AgentEngine


def _write_full_session_workspace(tmp_path: Path) -> Path:
    agent_dir = tmp_path / ".agent"
    skills_dir = agent_dir / "skills"
    workflows_dir = agent_dir / "workflows"
    memory_dir = agent_dir / "memory"
    knowledge_dir = agent_dir / "knowledge_base"

    for directory in (skills_dir, workflows_dir, memory_dir, knowledge_dir):
        directory.mkdir(parents=True, exist_ok=True)

    (skills_dir / "fake_tool.md").write_text(
        textwrap.dedent(
            """\
            ---
            id: fake_tool
            name: fake_tool
            description: Local integration-test skill.
            version: 1.0.0
            inputs:
              text:
                type: string
                required: true
            outputs:
              echo:
                type: string
            ---
            # fake_tool
            """
        ),
        encoding="utf-8",
    )
    (workflows_dir / "full_session.md").write_text(
        textwrap.dedent(
            """\
            ---
            name: full_session
            steps:
              - id: call_skill
                tool: fake_tool
                params:
                  text: "{{ inputs.topic }}"
              - id: remember_result
                action: remember
                depends_on: [call_skill]
                params:
                  key: workflow_result
                  value: "{{ call_skill.output.echo }}"
              - id: final_response
                action: respond
                depends_on: [remember_result]
                params:
                  status: complete
                  value: "{{ remember_result.value }}"
            ---
            # Full Session Workflow
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
            name: full-session-agent
            version: "0.1.0"
            purpose: Verify a full Portable Agent runtime loop.
            language: en-US
            authorization_level: interactive-approval
            use_case_tags: [integration]
            tools:
              - fake_tool
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
            ---
            # Full Session Agent
            """
        ),
        encoding="utf-8",
    )
    return config_path


def _register_fake_skill(engine: AgentEngine) -> None:
    def fake_tool(params: dict[str, Any]) -> dict[str, str]:
        return {"echo": f"processed:{params['text']}"}

    engine.router.register_tool("fake_tool", fake_tool)


def test_full_portable_agent_runtime_session(tmp_path: Path) -> None:
    config_path = _write_full_session_workspace(tmp_path)
    engine = AgentEngine(config_path)
    _register_fake_skill(engine)

    engine.memory.write("session_goal", "exercise full runtime loop")
    skill_result = engine.run("fake_tool", {"text": "PAP"})
    workflow_result = engine.execute_workflow("full_session", {"topic": "PAP"})
    handoff_id = engine.export_handoff(
        task_state="full session complete",
        pending_steps=["continue verification"],
        context_summary="Integration test exported runtime state.",
        memory_keys=["session_goal", "workflow_result"],
        handoff_id="integration-session",
    )

    receiving_engine = AgentEngine(config_path)
    imported_packet = receiving_engine.import_handoff(handoff_id)

    assert engine.config["name"] == "full-session-agent"
    assert skill_result == {"echo": "processed:PAP"}
    assert workflow_result["call_skill"]["output"] == {"echo": "processed:PAP"}
    assert workflow_result["remember_result"]["value"] == "processed:PAP"
    assert workflow_result["final_response"]["response"] == {
        "status": "complete",
        "value": "processed:PAP",
    }
    assert imported_packet["task_state"] == "full session complete"
    assert receiving_engine.memory.read("session_goal") == "exercise full runtime loop"
    assert receiving_engine.memory.read("workflow_result") == "processed:PAP"
