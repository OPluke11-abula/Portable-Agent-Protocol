"""Behavior tests for the opt-in evidence memory schema proposal."""

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


def test_evidence_memory_schema_accepts_layered_traceable_memory() -> None:
    evidence_memory = {
        "schema_version": "1.0.0",
        "memory_id": "incident_memory",
        "l0_raw_evidence_refs": [
            {
                "id": "ev-001",
                "kind": "file",
                "uri": "docs/reviews/incident.md",
                "result_ref": "sha256:" + "a" * 64,
            }
        ],
        "l1_atoms": [
            {
                "id": "atom-001",
                "claim": "The workflow linter validates governance checkpoints.",
                "trace_refs": [
                    {
                        "ref_type": "raw_evidence",
                        "ref_id": "ev-001",
                        "result_ref": "sha256:" + "a" * 64,
                    }
                ],
            }
        ],
        "l2_scenarios": [
            {
                "id": "scenario-001",
                "summary": "A governed workflow checkpoint can be resumed after validation.",
                "atom_refs": ["atom-001"],
                "trace_refs": [{"ref_type": "memory_atom", "ref_id": "atom-001"}],
            }
        ],
        "l3_profile": {
            "id": "profile-001",
            "persona": "programmer-agent",
            "claims": [
                {
                    "id": "profile-claim-001",
                    "claim": "Prefers schema-first workflow changes.",
                    "trace_refs": [{"ref_type": "memory_atom", "ref_id": "atom-001"}],
                }
            ],
        },
        "mermaid_canvases": [
            {
                "id": "canvas-001",
                "node_id": "triage_node",
                "result_ref": "sha256:" + "b" * 64,
                "trace_refs": [{"ref_type": "scenario", "ref_id": "scenario-001"}],
            }
        ],
    }

    jsonschema.validate(evidence_memory, _schema("evidence-memory.schema.json"))


def test_evidence_memory_schema_rejects_untraced_summarized_claims() -> None:
    evidence_memory = {
        "schema_version": "1.0.0",
        "memory_id": "untraced_memory",
        "l1_atoms": [
            {
                "id": "atom-001",
                "claim": "This summary has no source evidence.",
                "trace_refs": [],
            }
        ],
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(evidence_memory, _schema("evidence-memory.schema.json"))


def test_existing_memory_schema_remains_backward_compatible() -> None:
    semantic_memory = {
        "semantic": {
            "key": "workflow_linter",
            "value": "read-only governance validation",
        }
    }

    jsonschema.validate(semantic_memory, _schema("memory.schema.json"))
