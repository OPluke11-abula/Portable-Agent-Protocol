# Workflow Governance Scaffold

This note defines the Phase 6 governance layer for PAP workflows. It is
documentation-only: it does not install hooks, start daemons, execute workflow
stages, or change runtime behavior. Implementations MAY adopt these rules by
adding compatible schemas, linters, and validators in later Phase 6 tasks.

The opt-in schema surfaces for this governance layer are:

- `spec/workflow-manifest.schema.json`: stage, director, canonical artifact,
  allowed action, and approval policy metadata.
- `spec/workflow-checkpoint.schema.json`: checkpoint status, artifact hash,
  evidence references, verifier metadata, and unresolved risks.
- `docs/las-interop-validation-plan.md`: LAS consumption and verification plan
  for workflow, checkpoint, evidence memory, and review-gate fields.

Opt-in governance records are discovered by the workspace linter from:

- `.agent/workflows/governance/manifests/*.json`
- `.agent/workflows/governance/checkpoints/*.json`

The linter validates these records without executing workflow stages, tools, or
approval actions.

## Scope

The governance layer covers workflow source-of-truth order, risk policy, review
protocol, and handoff expectations for PAP-compatible agents. It preserves PAP's
Brain and Hands separation:

- Brain: `.agent/` manifests, workflow notes, routing rules, schemas, task state,
  and knowledge documents.
- Hands: stateless runtime tools, adapters, CLI commands, validators, and other
  executable code.

Governance documents must describe decisions and constraints. They must not
embed hidden runtime hooks, background capture, remote memory writes, or adapter
side effects.

## Source-of-Truth Order

When workflow behavior is ambiguous, resolve conflicts in this order:

1. Current user instruction and explicit approval boundaries.
2. Active handoff packet or handoff document for the current thread.
3. `.agent/agent.md` for persona, mounted capabilities, hard rules, and the
   canonical PAP entrypoint map.
4. `.agent/routing.md` for deterministic situation-to-skill routing.
5. `.agent/skills.md`, `.agent/workflows.md`, and per-skill or per-workflow
   contracts for callable capability and DAG definitions.
6. `agent_tasks.md` for current task state, dependencies, and completion status.
7. `spec/*.json` and protocol docs for schema compatibility and validation
   rules.
8. User-facing docs such as `README.md`, `USAGE.md`, and guides.

README files are explanatory surfaces for humans. They are not execution logs,
agent scratchpads, or the primary source of operational truth.

## Risk Policy

Workflow changes default to read-only and schema-first until the user explicitly
approves execution or external-state changes.

| Risk | Examples | Required handling |
| --- | --- | --- |
| Low | Protocol docs, examples, schema proposals, read-only lint rules | Keep changes narrow and run relevant validation. |
| Medium | Backward-compatible schema additions, CLI validators, local-only test fixtures | Add focused tests and preserve existing workspace compatibility. |
| High | Runtime execution changes, approval policy changes, memory capture, credential handling, cross-workspace writes | Require explicit review notes, validation evidence, and user approval before risky execution. |
| Critical | Destructive actions, global hooks, remote gateways, secret exposure, deploys, parallel audit agents by default | Block by default unless the user explicitly requests the action and the review gate records impact and rollback expectations. |

High-risk and critical workflow work must be report-only until a later approved
step performs the action. Secrets and credentials must be redacted in reports,
logs, examples, and handoffs.

## Review Protocol

Every workflow governance change should identify:

- Affected source of truth files.
- Whether the change is documentation-only, schema-only, validator-only, or
  runtime-affecting.
- Backward-compatibility impact for existing PAP workspaces.
- Verification commands actually run, with their observed results.
- Unresolved risks or follow-up tasks.

Reviewers should verify that protocol/runtime boundaries stay intact: core PAP
schemas and workflow rules must not depend on a specific adapter, CLI surface,
UI, generated artifact, or downstream LAS implementation. If a task adds a
review or security finding, the finding should include verdict, severity, source
trace, impact, remediation, and validation status using
`spec/review-findings.schema.json`.

## Handoff Expectations

Workflow handoffs remain compact coordination metadata. A handoff should include:

- `task_state`: exact current task status.
- `pending_steps`: immediate next actions, ordered and executable.
- `context_summary`: files changed, constraints accepted, and decisions made.
- `memory_snapshot`: small state markers or evidence references needed by the
  receiving agent.
- `checksum`: integrity hash for the canonical handoff payload when represented
  as a machine-readable packet.

Handoffs should reference large artifacts by path or evidence reference rather
than copying their full content. They must preserve the onboarding sequence from
`.agent/agent.md`, keep thread transitions within the 5 to 15 turn policy, and
avoid introducing background memory capture or external synchronization.

## Completion Checklist

Before a workflow governance task is marked complete:

- The relevant `.agent` registry or task manifest is updated.
- README remains free of internal task logs unless a user-facing capability
  changed.
- Verification was run and the command/result is recorded for the user.
- Later schema, linter, memory, and review-gate work remains opt-in and
  backward compatible.
