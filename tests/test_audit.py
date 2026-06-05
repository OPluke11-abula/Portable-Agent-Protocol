"""Tests for the PAP Agent Self-Audit diagnostic tool (Task 5-01)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agent_runtime import AgentEngine, AgentSelfAuditor
from agent_runtime.engine import load_agent_config


def _write_mock_workspace(tmp_path: Path, tool_version: str = "1.0.0", is_tool_malformed: bool = False) -> Path:
    agent_dir = tmp_path / ".agent"
    skills_dir = agent_dir / "skills"
    memory_dir = agent_dir / "memory"
    semantic_dir = memory_dir / "semantic"
    handoff_dir = memory_dir / "handoff"
    workflows_dir = agent_dir / "workflows"
    
    for directory in (skills_dir, memory_dir, semantic_dir, handoff_dir, workflows_dir):
        directory.mkdir(parents=True, exist_ok=True)

    # Create dummy entrypoints and directories to pass validate_agent_config_paths
    (agent_dir / "skills.md").write_text("", encoding="utf-8")
    (tmp_path / "agent_tasks.md").write_text("", encoding="utf-8")
    (agent_dir / "handoff_guide.md").write_text("", encoding="utf-8")
    (agent_dir / "knowledge_base").mkdir(parents=True, exist_ok=True)

    # Write a test skill contract
    if is_tool_malformed:
        (skills_dir / "test_tool.md").write_text("malformed content", encoding="utf-8")
    else:
        (skills_dir / "test_tool.md").write_text(f"""---
id: test_tool
name: test_tool
description: "A test tool"
version: "{tool_version}"
inputs: {{}}
outputs: {{}}
safety_notes: []
---
# test_tool
""", encoding="utf-8")

    # Write agent manifest config
    config_path = agent_dir / "agent.md"
    config_path.write_text(f"""---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: "self-audit-test"
version: "0.1.0"
purpose: "Test PAP self audit"
language: "en-US"
authorization_level: "autonomous"
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
  backend: "local"
  path: "{memory_dir.as_posix()}/"
---
# Test Onboarding
""", encoding="utf-8")
    
    return config_path


def test_audit_success_with_clean_workspace(tmp_path: Path) -> None:
    config_path = _write_mock_workspace(tmp_path)
    engine = AgentEngine(config_path, bypass_onboarding=True)
    auditor = AgentSelfAuditor(engine)
    report = auditor.run_audit()

    value = report["semantic"]["value"]
    assert value["summary"]["skills_checked"] == 1
    assert value["summary"]["skills_issues"] == 0
    assert len(value["issues"]) == 0
    assert len(value["recommendations"]) == 0

    # Verify report is written to disk
    report_file = tmp_path / ".agent" / "memory" / "semantic" / "audit_log.json"
    assert report_file.exists()
    saved_data = json.loads(report_file.read_text(encoding="utf-8"))
    assert saved_data["semantic"]["key"] == "audit_log"


def test_audit_detects_outdated_skill_version(tmp_path: Path) -> None:
    config_path = _write_mock_workspace(tmp_path, tool_version="0.8.0")
    engine = AgentEngine(config_path, bypass_onboarding=True)
    auditor = AgentSelfAuditor(engine)
    report = auditor.run_audit()

    value = report["semantic"]["value"]
    assert len(value["issues"]) == 1
    assert value["issues"][0]["type"] == "outdated_or_invalid_contract"
    assert "outdated" in value["issues"][0]["details"]
    assert len(value["recommendations"]) == 1
    assert value["recommendations"][0]["task_id"] == "upgrade_skill_version_test_tool"


def test_audit_detects_missing_skill_contract(tmp_path: Path) -> None:
    config_path = _write_mock_workspace(tmp_path)
    # Delete the contract file to simulate missing contract
    contract_file = tmp_path / ".agent" / "skills" / "test_tool.md"
    contract_file.unlink()

    from unittest.mock import patch
    with patch("agent_runtime.engine.validate_agent_config_paths"):
        engine = AgentEngine(config_path, bypass_onboarding=True)
    auditor = AgentSelfAuditor(engine)
    report = auditor.run_audit()

    value = report["semantic"]["value"]
    assert len(value["issues"]) == 1
    assert value["issues"][0]["type"] == "missing_contract"
    assert len(value["recommendations"]) == 1
    assert value["recommendations"][0]["task_id"] == "create_skill_contract_test_tool"


def test_audit_detects_malformed_skill_contract(tmp_path: Path) -> None:
    config_path = _write_mock_workspace(tmp_path, is_tool_malformed=True)
    engine = AgentEngine(config_path, bypass_onboarding=True)
    auditor = AgentSelfAuditor(engine)
    report = auditor.run_audit()

    value = report["semantic"]["value"]
    assert len(value["issues"]) >= 1
    types = [issue["type"] for issue in value["issues"]]
    assert "outdated_or_invalid_contract" in types


def test_audit_detects_memory_bloat_and_handoff_limits(tmp_path: Path) -> None:
    config_path = _write_mock_workspace(tmp_path)
    # Write a mock memory.json that exceeds threshold limit
    mem_dir = tmp_path / ".agent" / "memory"
    memory_file = mem_dir / "memory.json"
    memory_file.write_text("a" * 500, encoding="utf-8")  # Write 500 bytes

    # Populate too many handoff files
    handoff_dir = mem_dir / "handoff"
    for idx in range(6):
        (handoff_dir / f"handoff_{idx}.json").write_text("{}", encoding="utf-8")

    engine = AgentEngine(config_path, bypass_onboarding=True)
    auditor = AgentSelfAuditor(
        engine,
        memory_size_threshold=200,      # Set small threshold of 200 bytes
        handoff_count_threshold=5,      # Set small threshold of 5 files
    )
    report = auditor.run_audit()

    value = report["semantic"]["value"]
    issues_types = [issue["type"] for issue in value["issues"]]
    assert "memory_size_exceeded" in issues_types
    assert "too_many_handoff_files" in issues_types
    assert len(value["recommendations"]) >= 2


def test_audit_detects_abandoned_workflows(tmp_path: Path) -> None:
    config_path = _write_mock_workspace(tmp_path)
    # Write a mock workflow session file inside runs/
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    run_file = runs_dir / "wf_session_abandoned.json"
    
    session_data = {
        "workflow_id": "test_wf",
        "session_id": "wf_session_abandoned",
        "status": "running",
        "inputs": {},
        "step_states": {},
        "context": {}
    }
    run_file.write_text(json.dumps(session_data), encoding="utf-8")

    # Set file modification time to 48 hours ago
    back_then = time.time() - (48 * 3600)
    os.utime(str(run_file), (back_then, back_then))

    engine = AgentEngine(config_path, bypass_onboarding=True)
    auditor = AgentSelfAuditor(
        engine,
        workflow_abandoned_threshold_seconds=12 * 3600  # 12 hours limit
    )
    report = auditor.run_audit()

    value = report["semantic"]["value"]
    assert len(value["issues"]) == 1
    assert value["issues"][0]["type"] == "abandoned_workflow_run"
    assert value["issues"][0]["id"] == "wf_session_abandoned"
    assert len(value["recommendations"]) == 1
    assert value["recommendations"][0]["task_id"] == "cleanup_workflow_session_wf_session_abandoned"


def test_cli_self_audit_integration(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    config_path = _write_mock_workspace(tmp_path)
    
    # We invoke cli.py main using sys.argv mocks
    import sys
    from cli import main

    orig_argv = sys.argv
    sys.argv = ["cli.py", "--config", str(config_path), "--self-audit", "--bypass-onboarding"]
    try:
        ret = main()
        assert ret == 0
    finally:
        sys.argv = orig_argv

    captured = capsys.readouterr()
    assert "PAP SELF-AUDIT REPORT" in captured.out
    assert "No workspace health issues detected" in captured.out
