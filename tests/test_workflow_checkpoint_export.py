"""Tests for Workflow File Checkpoint Exporter (Task 1-09).

Verifies that workflow sessions produce physical runs/<session_id>.json files
alongside the in-memory persistence, enabling external tools and CLI resume.
"""

from __future__ import annotations

import json
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
    (workflows_dir / "sample.md").write_text(
        textwrap.dedent(workflow_body), encoding="utf-8"
    )

    config = textwrap.dedent(
        """\
        ---
        protocol_version: "1.0.0"
        min_runtime_version: "0.1.0"
        name: test-agent
        version: "0.1.0"
        purpose: Test checkpoint export.
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


SIMPLE_WORKFLOW = """\
---
name: sample
steps:
  - id: step_one
    tool: fake_tool
    params:
      val: "hello"
  - id: step_two
    action: respond
    depends_on: [step_one]
    params:
      msg: "done"
---
# Sample Workflow
"""


def test_runs_file_created_on_workflow_execution(tmp_path: Path) -> None:
    """Verify that runs/<session_id>.json is created when a workflow runs."""
    config_path = _write_workspace(tmp_path, SIMPLE_WORKFLOW)
    engine = AgentEngine(config_path)
    engine.router.register_tool("fake_tool", lambda params: {"out": params["val"]})

    wf_engine = WorkflowEngine(engine)
    wf_engine.run("sample", {"topic": "test"})

    runs_dir = tmp_path / "runs"
    assert runs_dir.exists(), "runs/ directory should be created"
    json_files = list(runs_dir.glob("*.json"))
    assert len(json_files) == 1, "Exactly one session JSON file should exist"


def test_runs_file_contains_valid_session_state(tmp_path: Path) -> None:
    """Verify the exported JSON contains correct session structure and step states."""
    config_path = _write_workspace(tmp_path, SIMPLE_WORKFLOW)
    engine = AgentEngine(config_path)
    engine.router.register_tool("fake_tool", lambda params: {"out": params["val"]})

    wf_engine = WorkflowEngine(engine)
    wf_engine.run("sample", {"topic": "test"})

    runs_dir = tmp_path / "runs"
    json_files = list(runs_dir.glob("*.json"))
    session_data = json.loads(json_files[0].read_text(encoding="utf-8"))

    assert session_data["workflow_id"] == "sample"
    assert session_data["status"] == "success"
    assert "step_states" in session_data
    assert session_data["step_states"]["step_one"]["status"] == "success"
    assert session_data["step_states"]["step_two"]["status"] == "success"


def test_runs_file_updated_idempotently(tmp_path: Path) -> None:
    """Verify the session file is overwritten on each save, not duplicated."""
    config_path = _write_workspace(tmp_path, SIMPLE_WORKFLOW)
    engine = AgentEngine(config_path)
    engine.router.register_tool("fake_tool", lambda params: {"out": params["val"]})

    wf_engine = WorkflowEngine(engine)
    wf_engine.run("sample", {}, session_id="fixed_session_001")

    runs_dir = tmp_path / "runs"
    json_files = list(runs_dir.glob("*.json"))
    assert len(json_files) == 1
    assert json_files[0].name == "fixed_session_001.json"

    # Run again with same session_id — file should be overwritten, not duplicated
    wf_engine.run("sample", {}, session_id="fixed_session_001")
    json_files_after = list(runs_dir.glob("*.json"))
    assert len(json_files_after) == 1


def test_runs_file_reflects_failure_state(tmp_path: Path) -> None:
    """Verify failed workflow sessions produce a file with failed/skipped states."""
    workflow_body = """\
    ---
    name: sample
    steps:
      - id: step_one
        tool: fake_tool
        params:
          val: "ok"
      - id: step_two
        tool: fake_tool
        depends_on: [step_one]
        params:
          val: "boom"
      - id: step_three
        action: respond
        depends_on: [step_two]
        params:
          msg: "never"
    ---
    # Sample Workflow
    """
    config_path = _write_workspace(tmp_path, workflow_body)
    engine = AgentEngine(config_path)

    def mock_tool(params):
        if params.get("val") == "boom":
            raise ValueError("Intentional failure")
        return {"out": params["val"]}

    engine.router.register_tool("fake_tool", mock_tool)

    wf_engine = WorkflowEngine(engine)
    with pytest.raises(ValueError, match="Workflow execution failed"):
        wf_engine.run("sample", {})

    runs_dir = tmp_path / "runs"
    json_files = list(runs_dir.glob("*.json"))
    assert len(json_files) == 1

    session_data = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert session_data["status"] == "failed"
    assert session_data["step_states"]["step_one"]["status"] == "success"
    assert session_data["step_states"]["step_two"]["status"] == "failed"
    assert session_data["step_states"]["step_three"]["status"] == "skipped"


def test_resume_from_exported_file(tmp_path: Path) -> None:
    """End-to-end: fail → export to file → fix → resume from file → success."""
    workflow_body = """\
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
          val: "retry_me"
    ---
    # Sample Workflow
    """
    config_path = _write_workspace(tmp_path, workflow_body)
    engine = AgentEngine(config_path)

    should_fail = True

    def mock_tool(params):
        nonlocal should_fail
        if params.get("val") == "retry_me" and should_fail:
            raise ValueError("First attempt failed")
        return {"out": params["val"]}

    engine.router.register_tool("fake_tool", mock_tool)

    wf_engine = WorkflowEngine(engine)

    # 1. First run fails
    with pytest.raises(ValueError, match="Workflow execution failed"):
        wf_engine.run("sample", {}, session_id="resume_test_001")

    # 2. Read the exported file
    runs_dir = tmp_path / "runs"
    session_file = runs_dir / "resume_test_001.json"
    assert session_file.exists()
    exported = json.loads(session_file.read_text(encoding="utf-8"))
    assert exported["status"] == "failed"

    # 3. Fix the error and resume
    should_fail = False
    result = engine.resume_workflow("sample", "resume_test_001")

    assert result["step_one"]["output"] == {"out": "start"}
    assert result["step_two"]["output"] == {"out": "retry_me"}

    # 4. Verify the file now reflects success
    exported_after = json.loads(session_file.read_text(encoding="utf-8"))
    assert exported_after["status"] == "success"
