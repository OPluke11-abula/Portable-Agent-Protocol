"""Tests for workflow DAG parsing and execution."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from agent_runtime.engine import AgentEngine
from agent_runtime.workflow import WorkflowExecutor


def _write_workspace(tmp_path: Path, workflow_body: str) -> Path:
    agent_dir = tmp_path / ".agent"
    workflows_dir = agent_dir / "workflows"
    skills_dir = agent_dir / "skills"
    workflows_dir.mkdir(parents=True)
    skills_dir.mkdir()
    (skills_dir / "fake_search.md").write_text("# fake_search\n", encoding="utf-8")
    (workflows_dir / "sample.md").write_text(textwrap.dedent(workflow_body), encoding="utf-8")

    config = textwrap.dedent(
        """\
        ---
        protocol_version: "1.0.0"
        min_runtime_version: "0.1.0"
        name: test-agent
        version: "0.1.0"
        purpose: Test workflow execution.
        language: en-US
        authorization_level: interactive-approval
        use_case_tags: [test]
        tools:
          - fake_search
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


def test_workflow_executes_steps_in_dependency_order(tmp_path: Path) -> None:
    config_path = _write_workspace(
        tmp_path,
        """\
        ---
        name: sample
        steps:
          - id: search
            tool: fake_search
            params:
              query: "{{ inputs.topic }}"
          - id: store
            action: remember
            depends_on: [search]
            params:
              key: result
              value: "{{ search.output }}"
          - id: reply
            action: respond
            depends_on: [store]
            params:
              saved: "{{ store.status }}"
        ---
        # Sample Workflow
        """,
    )
    engine = AgentEngine(config_path)
    engine.router.register_tool(
        "fake_search", lambda params: {"items": [f"result for {params['query']}"]}
    )

    result = engine.execute_workflow("sample", {"topic": "PAP"})

    assert result["search"]["output"] == {"items": ["result for PAP"]}
    assert engine.memory.read("result") == {"items": ["result for PAP"]}
    assert result["reply"]["response"] == {"saved": "success"}


def test_workflow_rejects_cycles(tmp_path: Path) -> None:
    config_path = _write_workspace(
        tmp_path,
        """\
        ---
        name: sample
        steps:
          - id: a
            action: respond
            depends_on: [b]
            params: {}
          - id: b
            action: respond
            depends_on: [a]
            params: {}
        ---
        # Sample Workflow
        """,
    )
    engine = AgentEngine(config_path)
    dag = WorkflowExecutor(engine).load("sample")

    with pytest.raises(ValueError, match="Cycle detected"):
        dag.topological_sort()
