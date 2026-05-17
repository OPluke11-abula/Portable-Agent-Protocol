---
name: run_and_explain
steps:
  - id: execute
    tool: code_executor
    params:
      code: "{{ inputs.code }}"
  - id: explain
    action: respond
    depends_on: [execute]
    params:
      template: task_complete
      result: "{{ execute.output }}"
---

# Workflow Note: run_and_explain

Canonical registry entry: `.agent/workflows.md`

## Purpose

Execute a code snippet and explain the result in a user-facing response.

## Inputs

- `code`

## Outputs
---
name: run_and_explain
steps:
  - id: execute
    tool: code_executor
    params:
      code: "{{ inputs.code }}"
  - id: explain
    action: respond
    depends_on: [execute]
    params:
      template: task_complete
      result: "{{ execute.output }}"
---

# Workflow Note: run_and_explain

Canonical registry entry: `.agent/workflows.md`

## Purpose

Execute a code snippet and explain the result in a user-facing response.

## Inputs

- `code`

## Outputs

- Execution result from `code_executor`
- Final explanation using the completion prompt

## Maintenance Notes

- Keep the executable DAG definition in the YAML front matter of this file.
- Use this file's body for rationale, usage notes, and future extension ideas.
