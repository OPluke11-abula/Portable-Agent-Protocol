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

- Keep the executable step sequence in `.agent/workflows.md`
- Use this file for rationale, usage notes, and guardrail discussion
