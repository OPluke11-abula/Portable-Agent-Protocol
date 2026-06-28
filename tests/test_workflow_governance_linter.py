"""Workspace linter coverage for opt-in workflow governance records."""

from __future__ import annotations

import json
from pathlib import Path

from agent_runtime.lint import WorkspaceLinter


def _copy_spec_schemas(tmp_path: Path) -> None:
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir(exist_ok=True)
    original_root = Path(__file__).parent.parent
    for schema_file in original_root.glob("spec/*.json"):
        (spec_dir / schema_file.name).write_text(
            schema_file.read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def _write_minimal_workspace(tmp_path: Path) -> Path:
    _copy_spec_schemas(tmp_path)
    agent_dir = tmp_path / ".agent"
    (agent_dir / "skills").mkdir(parents=True)
    (agent_dir / "workflows").mkdir()
    (agent_dir / "knowledge_base").mkdir()
    (agent_dir / "prompts").mkdir()
    (agent_dir / "memory").mkdir()

    agent_md = agent_dir / "agent.md"
    agent_md.write_text(
        """---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: "test-agent"
version: "0.1.0"
purpose: "test"
language: "en-US"
authorization_level: "interactive-approval"
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
# Test Agent
""",
        encoding="utf-8",
    )
    for catalog in ("skills.md", "prompts.md", "memory.md", "workflows.md"):
        (agent_dir / catalog).write_text('---\nschema_version: "1.0.0"\n---\n', encoding="utf-8")
    return agent_md


def test_linter_accepts_valid_governance_manifest_and_checkpoint(tmp_path: Path) -> None:
    agent_md = _write_minimal_workspace(tmp_path)
    governance_dir = tmp_path / ".agent" / "workflows" / "governance"
    manifests_dir = governance_dir / "manifests"
    checkpoints_dir = governance_dir / "checkpoints"
    manifests_dir.mkdir(parents=True)
    checkpoints_dir.mkdir()

    (manifests_dir / "incident_review.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "workflow_id": "incident_review",
                "stages": [
                    {
                        "id": "triage",
                        "director": {"role": "programmer"},
                        "canonical_artifacts": [
                            {"id": "triage_report", "path": "docs/reviews/triage.md", "kind": "report"}
                        ],
                        "allowed_actions": ["read", "validate", "report"],
                        "approval_policy": {"mode": "interactive", "required_for": ["write"]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (checkpoints_dir / "triage-001.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "checkpoint_id": "triage-001",
                "workflow_id": "incident_review",
                "stage_id": "triage",
                "artifact_hash": "sha256:" + "a" * 64,
                "evidence_refs": [{"id": "ev-001", "kind": "file", "uri": "docs/reviews/triage.md"}],
                "verifier": {"type": "command", "value": ".\\.venv\\bin\\python.exe -m pytest --no-cov -q"},
                "unresolved_risks": [],
                "status": "passed",
            }
        ),
        encoding="utf-8",
    )

    issues = WorkspaceLinter(agent_md).run_all_checks()

    assert not [issue for issue in issues if "workflow governance" in issue.message.lower()]


def test_linter_rejects_invalid_governance_records(tmp_path: Path) -> None:
    agent_md = _write_minimal_workspace(tmp_path)
    governance_dir = tmp_path / ".agent" / "workflows" / "governance"
    manifests_dir = governance_dir / "manifests"
    checkpoints_dir = governance_dir / "checkpoints"
    manifests_dir.mkdir(parents=True)
    checkpoints_dir.mkdir()

    (manifests_dir / "bad_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "workflow_id": "bad_manifest",
                "stages": [
                    {
                        "id": "triage",
                        "director": {"role": "programmer"},
                        "canonical_artifacts": [
                            {"id": "escaped", "path": "../outside.md", "kind": "report"}
                        ],
                        "allowed_actions": ["read"],
                        "approval_policy": {"mode": "interactive"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (checkpoints_dir / "bad_checkpoint.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "checkpoint_id": "bad-checkpoint",
                "workflow_id": "bad_manifest",
                "stage_id": "triage",
                "artifact_hash": "sha256:" + "b" * 64,
                "evidence_refs": [],
                "verifier": {"type": "command", "value": "pytest"},
                "unresolved_risks": [],
                "status": "mostly_done",
            }
        ),
        encoding="utf-8",
    )

    issues = WorkspaceLinter(agent_md).run_all_checks()
    messages = [issue.message for issue in issues]

    assert any("escapes the workspace" in message for message in messages)
    assert any("schema validation error" in message and "mostly_done" in message for message in messages)
    assert any("schema validation error" in message and "evidence_refs" in message for message in messages)


def test_linter_keeps_legacy_workflows_backward_compatible(tmp_path: Path) -> None:
    agent_md = _write_minimal_workspace(tmp_path)
    (tmp_path / ".agent" / "workflows" / "sample.md").write_text(
        """---
name: "sample"
steps:
  - id: "reply"
    action: "respond"
    params: {}
---
# Sample
""",
        encoding="utf-8",
    )

    issues = WorkspaceLinter(agent_md).run_all_checks()

    assert not [issue for issue in issues if issue.severity == "error"]
