"""Behavior tests for opt-in workflow governance schemas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    import jsonschema
except ImportError:
    jsonschema = None


pytestmark = pytest.mark.skipif(jsonschema is None, reason="jsonschema package not installed")


def _schema(name: str) -> dict:
    return json.loads((Path("spec") / name).read_text(encoding="utf-8"))


def test_workflow_manifest_schema_accepts_governed_opt_in_manifest() -> None:
    manifest = {
        "schema_version": "1.0.0",
        "workflow_id": "incident_review",
        "stages": [
            {
                "id": "triage",
                "director": {
                    "role": "programmer",
                    "responsibilities": ["classify risk", "collect evidence"],
                },
                "canonical_artifacts": [
                    {
                        "id": "triage_report",
                        "path": "docs/reviews/triage.md",
                        "kind": "report",
                    }
                ],
                "allowed_actions": ["read", "validate", "report"],
                "approval_policy": {
                    "mode": "interactive",
                    "required_for": ["write", "external_state"],
                },
            }
        ],
    }

    jsonschema.validate(manifest, _schema("workflow-manifest.schema.json"))


def test_workflow_checkpoint_schema_requires_status_and_evidence_refs() -> None:
    valid_checkpoint = {
        "schema_version": "1.0.0",
        "checkpoint_id": "triage-001",
        "workflow_id": "incident_review",
        "stage_id": "triage",
        "artifact_hash": "sha256:" + "a" * 64,
        "evidence_refs": [
            {
                "id": "ev-001",
                "kind": "file",
                "uri": "docs/reviews/triage.md",
            }
        ],
        "verifier": {
            "type": "command",
            "value": ".\\.venv\\bin\\python.exe -m pytest --no-cov -q",
        },
        "unresolved_risks": [],
        "status": "passed",
    }

    checkpoint_schema = _schema("workflow-checkpoint.schema.json")
    jsonschema.validate(valid_checkpoint, checkpoint_schema)

    missing_evidence = dict(valid_checkpoint)
    missing_evidence["evidence_refs"] = []
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(missing_evidence, checkpoint_schema)

    invalid_status = dict(valid_checkpoint)
    invalid_status["status"] = "mostly_done"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid_status, checkpoint_schema)


def test_legacy_workflow_schema_remains_minimal_and_backward_compatible() -> None:
    legacy_workflow = {
        "name": "run_and_explain",
        "steps": [
            {
                "id": "execute",
                "tool": "code_executor",
                "params": {"code": "{{ inputs.code }}"},
            }
        ],
    }

    jsonschema.validate(legacy_workflow, _schema("workflow.schema.json"))
