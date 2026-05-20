"""Tests for stateful WorkflowEngine execution, checkpointing, and resumption."""

from __future__ import annotations

import textwrap
from pathlib import Path
import pytest

from agent_runtime.engine import AgentEngine
from agent_runtime.workflow_engine import WorkflowEngine, WorkflowSession


def _write_workspace(tmp_path: Path, workflow_body: str) -> Path:
    agent_dir = tmp_path / ".agent"
    workflows_dir = agent_dir / "workflows"
    skills_dir = agent_dir / "skills"
    workflows_dir.mkdir(parents=True)
    skills_dir.mkdir()
    (skills_dir / "fake_tool.md").write_text("# fake_tool\n", encoding="utf-8")
    (workflows_dir / "sample.md").write_text(textwrap.dedent(workflow_body), encoding="utf-8")

    config = textwrap.dedent(
        """\
        ---
        protocol_version: "1.0.0"
        min_runtime_version: "0.1.0"
        name: test-agent
        version: "0.1.0"
        purpose: Test workflow engine execution.
        language: en-US
        authorization_level: interactive-approval
        use_case_tags: [test]
        tools:
          - fake_tool
        protocol:
          root: .agent/
          manifest: .agent/agent.md
          directories:
            skills: .agent/skills/
            workflows: .agent/workflows/
        memory:
          backend: in_memory
        ---
        # Test Agent
        """
    )
    path = agent_dir / "agent.md"
    path.write_text(config, encoding="utf-8")
    return path


def test_workflow_engine_success_flow(tmp_path: Path) -> None:
    config_path = _write_workspace(
        tmp_path,
        """\
        ---
        name: sample
        steps:
          - id: step_one
            tool: fake_tool
            params:
              val: "{{ inputs.topic }}"
          - id: step_two
            action: remember
            depends_on: [step_one]
            params:
              key: "saved_topic"
              value: "{{ step_one.output.processed }}"
          - id: step_three
            action: respond
            depends_on: [step_two]
            params:
              msg: "Stored successfully"
        ---
        # Sample Workflow
        """,
    )
    engine = AgentEngine(config_path)
    engine.router.register_tool(
        "fake_tool", lambda params: {"processed": f"PROCESSED_{params['val']}"}
    )

    wf_engine = WorkflowEngine(engine)
    result = wf_engine.run("sample", {"topic": "antigravity"})

    # Verify context outputs
    assert result["step_one"]["output"] == {"processed": "PROCESSED_antigravity"}
    assert result["step_two"] == {"status": "success", "value": "PROCESSED_antigravity"}
    assert result["step_three"]["response"] == {"msg": "Stored successfully"}

    # Verify state persistence in memory
    assert engine.memory.read("saved_topic") == "PROCESSED_antigravity"

    # Find the session state key and load it
    session_keys = [k for k in engine.memory.list_keys() if k.startswith("workflow:sample:session:")]
    assert len(session_keys) == 1
    session_data = engine.memory.read(session_keys[0])
    assert session_data["status"] == "success"
    assert session_data["step_states"]["step_one"]["status"] == "success"
    assert session_data["step_states"]["step_two"]["status"] == "success"
    assert session_data["step_states"]["step_three"]["status"] == "success"


def test_workflow_engine_failure_propagation(tmp_path: Path) -> None:
    config_path = _write_workspace(
        tmp_path,
        """\
        ---
        name: sample
        steps:
          - id: step_one
            tool: fake_tool
            params:
              val: "start"
          - id: step_two
            tool: fake_tool
            depends_on: [step_one]
            params:
              val: "fail"
          - id: step_three
            action: respond
            depends_on: [step_two]
            params:
              msg: "Never runs"
        ---
        # Sample Workflow
        """,
    )
    engine = AgentEngine(config_path)

    # Make the tool fail when the value is "fail"
    def mock_tool(params):
        if params.get("val") == "fail":
            raise ValueError("Intentional tool failure")
        return {"processed": params["val"]}

    engine.router.register_tool("fake_tool", mock_tool)

    wf_engine = WorkflowEngine(engine)
    with pytest.raises(ValueError, match="Workflow execution failed at step 'step_two'"):
        wf_engine.run("sample", {})

    # Check persistence and skip logic
    session_keys = [k for k in engine.memory.list_keys() if k.startswith("workflow:sample:session:")]
    assert len(session_keys) == 1
    session_data = engine.memory.read(session_keys[0])
    assert session_data["status"] == "failed"
    assert session_data["step_states"]["step_one"]["status"] == "success"
    assert session_data["step_states"]["step_two"]["status"] == "failed"
    assert "Intentional tool failure" in session_data["step_states"]["step_two"]["error"]
    assert session_data["step_states"]["step_three"]["status"] == "skipped"

    # Check error writeback in persistent memory
    err_key = f"workflow_error:sample:step_two"
    err_log = engine.memory.read(err_key)
    assert err_log is not None
    assert err_log["workflow_id"] == "sample"
    assert err_log["step_id"] == "step_two"
    assert "Intentional tool failure" in err_log["error"]


def test_workflow_engine_checkpoint_resumption(tmp_path: Path) -> None:
    config_path = _write_workspace(
        tmp_path,
        """\
        ---
        name: sample
        steps:
          - id: step_one
            tool: fake_tool
            params:
              val: "start"
          - id: step_two
            tool: fake_tool
            depends_on: [step_one]
            params:
              val: "fail_first"
          - id: step_three
            tool: fake_tool
            depends_on: [step_two]
            params:
              val: "finish"
        ---
        # Sample Workflow
        """,
    )
    engine = AgentEngine(config_path)

    should_fail = True

    def mock_tool(params):
        nonlocal should_fail
        val = params.get("val")
        if val == "fail_first" and should_fail:
            raise ValueError("First execution failed")
        return {"processed": val}

    engine.router.register_tool("fake_tool", mock_tool)

    wf_engine = WorkflowEngine(engine)
    
    # 1. First execution fails at step_two
    with pytest.raises(ValueError, match="Workflow execution failed at step 'step_two'"):
        wf_engine.run("sample", {})

    session_keys = [k for k in engine.memory.list_keys() if k.startswith("workflow:sample:session:")]
    assert len(session_keys) == 1
    session_id = session_keys[0].split(":")[-1]

    # Verify first state before resumption
    session_data = engine.memory.read(session_keys[0])
    assert session_data["status"] == "failed"
    assert session_data["step_states"]["step_one"]["status"] == "success"
    assert session_data["step_states"]["step_two"]["status"] == "failed"
    assert session_data["step_states"]["step_three"]["status"] == "skipped"

    # 2. Fix the error trigger and resume
    should_fail = False
    
    # We resume the workflow using engine.resume_workflow
    result = engine.resume_workflow("sample", session_id)

    # 3. Check that it completed successfully
    assert result["step_one"]["output"] == {"processed": "start"}
    assert result["step_two"]["output"] == {"processed": "fail_first"}
    assert result["step_three"]["output"] == {"processed": "finish"}

    # Verify final states in memory
    session_data = engine.memory.read(session_keys[0])
    assert session_data["status"] == "success"
    assert session_data["step_states"]["step_one"]["status"] == "success"
    assert session_data["step_states"]["step_two"]["status"] == "success"
    assert session_data["step_states"]["step_three"]["status"] == "success"
