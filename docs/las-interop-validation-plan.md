# LAS Interop Validation Plan

This plan defines how LAS should consume the Phase 6 PAP workflow governance,
checkpoint, evidence memory, and review-gate fields. It is a validation plan,
not a runtime bridge. It does not change provider selection, start background
memory capture, enable parallel audit agents, or execute LAS actions from PAP.

Source context: `D:\GitHub\LLM-Agent-System\docs\architecture\las-pap-collaboration-memory-security-plan.md`.

## PAP Artifacts

LAS integration should treat these PAP artifacts as the portable contract:

- `spec/workflow-manifest.schema.json`
- `spec/workflow-checkpoint.schema.json`
- `spec/evidence-memory.schema.json`
- `spec/review-findings.schema.json`
- `.agent/workflows/governance/manifests/*.json`
- `.agent/workflows/governance/checkpoints/*.json`

Existing `.agent/workflows/*.md` DAG files remain valid. New governance fields
are opt-in unless a workspace adds governance manifest or checkpoint records.

## Field Consumption

| PAP field or artifact | LAS consumer | Validation expectation |
| --- | --- | --- |
| `workflow_id`, `stage_id`, `checkpoint_id` | `ConductorPlan` | May be serialized as workflow metadata without changing provider selection or routing behavior. |
| `artifact_hash`, `status`, `verifier`, `unresolved_risks` | `ConductorPlan`, `AuditLedger` | Checkpoints can be recorded as resumable stage state and audit evidence. |
| `evidence_refs`, `result_ref`, `node_id` | `LongTermMemoryStore`, `AuditLedger` | Memory summaries and audit decisions must retain traceable evidence pointers. |
| `l0_raw_evidence_refs`, `l1_atoms`, `l2_scenarios`, `l3_profile` | `LongTermMemoryStore` | LAS can map these to evidence, atom, scenario, and persona record types without replacing raw evidence. |
| `verdict`, `severity`, `source_trace`, `impact`, `remediation`, `validation_status` | `UnifiedPolicyGate`, `AuditLedger` | Review/security findings are report-only inputs to policy decisions and audit logs. |
| `exploit_path` for high or critical findings | `UnifiedPolicyGate` | High-risk findings require both exploit path and impact before escalation is considered valid. |

## Compatibility Checks

### ConductorPlan

- Accept optional workflow metadata fields without requiring them on ordinary
  plans.
- Preserve existing provider selection and tool routing behavior when workflow
  metadata is absent.
- Serialize workflow fields to stable JSON when present:
  `workflow_id`, `stage_id`, `checkpoint_ref`, and `evidence_refs`.

### LongTermMemoryStore

- Preserve existing `routing_outcome` records.
- Accept evidence-memory records as optional typed payloads:
  `evidence_ref`, `workflow_atom`, `workflow_scenario`, and
  `workflow_persona`.
- Reject summarized memory records that lack a raw evidence reference,
  canonical artifact reference, or lower-level traced memory reference.

### UnifiedPolicyGate

- Treat `review-findings.schema.json` reports as report-only evidence.
- Require explicit user approval before any external-state action, deploy,
  destructive operation, or parallel audit agent run.
- Reject high or critical security findings that omit `exploit_path` or
  `impact`.

### AuditLedger

- Record checkpoint validation, policy-gate decisions, and review/security
  findings with stable evidence references.
- Store hashes, refs, counts, and summaries. Do not copy raw secret-bearing
  output into audit records.
- Preserve `result_ref` and `node_id` when Mermaid canvas state is used.

## PAP Verification

Run these from `D:\GitHub\Portable-Agent-Protocol` before claiming the PAP side
is ready:

```powershell
.\.venv\bin\python.exe -m pytest --no-cov -q
.\.venv\bin\python.exe cli.py lint
git diff --check
```

Expected result:

- Full pytest passes.
- Workspace lint reports no issues.
- `git diff --check` reports no whitespace errors. Line-ending normalization
  warnings should be reported separately from real whitespace failures.

## LAS Verification

Run these from `D:\GitHub\LLM-Agent-System` before claiming LAS interop is ready:

```powershell
python agent_workspace/pap_validate.py
python agent_workspace/tool_manifest.py validate
.\scripts\verify.cmd -SkipViewer
```

Expected result:

- PAP validation still accepts the LAS `.agent` workspace.
- Tool manifest validation passes with any workflow-aware metadata treated as
  optional unless an opt-in manifest requires it.
- `scripts\verify.cmd -SkipViewer` passes.

## Ready Criteria

Declare the protocol extension ready only when:

- PAP schema and linter tests pass.
- LAS PAP validation and tool manifest validation pass.
- Workflow metadata remains optional for existing runs.
- Memory summaries trace back to raw evidence or canonical artifacts.
- Review/security findings are report-only by default.
- `UnifiedPolicyGate` and `AuditLedger` can consume review-gate fields without
  enabling parallel audit agents by default.
