"""Behavior tests for structured review and security findings schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    import jsonschema
except ImportError:
    jsonschema = None


pytestmark = pytest.mark.skipif(jsonschema is None, reason="jsonschema package not installed")


def _schema() -> dict:
    return json.loads(Path("spec/review-findings.schema.json").read_text(encoding="utf-8"))


def _base_report() -> dict:
    return {
        "schema_version": "1.0.0",
        "report_id": "review-001",
        "review_type": "security",
        "execution_policy": {
            "mode": "report_only",
            "parallel_audit_agents": False,
        },
        "findings": [
            {
                "id": "finding-001",
                "verdict": "fail",
                "severity": "high",
                "title": "Untrusted path reaches file read",
                "source_trace": [
                    {
                        "file": "agent_runtime/router.py",
                        "line": 42,
                        "evidence_ref": "ev-001",
                    }
                ],
                "impact": "An attacker could read files outside the workspace.",
                "exploit_path": {
                    "preconditions": ["Untrusted skill id is accepted"],
                    "steps": ["Submit a traversal path", "Observe file contents"],
                },
                "remediation": "Reject path separators and parent directory references.",
                "validation_status": "validated",
            }
        ],
    }


def test_review_findings_schema_accepts_structured_security_report() -> None:
    jsonschema.validate(_base_report(), _schema())


def test_review_findings_schema_requires_exploit_path_for_high_and_critical() -> None:
    report = _base_report()
    del report["findings"][0]["exploit_path"]

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(report, _schema())


def test_review_findings_schema_keeps_parallel_audit_agents_disabled_by_default() -> None:
    report = _base_report()
    report["execution_policy"]["parallel_audit_agents"] = True

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(report, _schema())


def test_review_findings_schema_accepts_medium_finding_without_exploit_path() -> None:
    report = _base_report()
    report["findings"][0]["severity"] = "medium"
    del report["findings"][0]["exploit_path"]

    jsonschema.validate(report, _schema())
