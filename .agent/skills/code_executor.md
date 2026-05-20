---
id: code_executor
name: code_executor
description: Execute small, bounded code or shell tasks inside the runtime's configured sandbox.
version: 1.0.0
inputs:
  runtime:
    type: string
    description: Execution runtime or shell.
    required: true
  command:
    type: string
    description: Command or code snippet to run.
    required: true
  working_directory:
    type: string
    description: Directory where execution should happen.
    required: false
  sandbox_policy:
    type: string
    description: Permissions, network access, and filesystem boundaries.
    required: false
outputs:
  stdout:
    type: string
    description: Captured standard output.
  stderr:
    type: string
    description: Captured standard error.
  exit_code:
    type: integer
    description: Process exit code.
  artifacts:
    type: array
    description: Any generated files or paths that matter to the workflow.
safety_notes:
  - Do not run destructive commands unless the workflow explicitly authorizes them.
  - Keep execution scoped to the declared working directory and sandbox policy.
  - Return non-zero exits as structured results rather than suppressing errors.
author: pap
---

# Skill: code_executor

Execute small, bounded code or shell tasks inside the runtime's configured
sandbox.

## Purpose

Use this skill when a workflow needs deterministic local execution, such as a
syntax check, unit test, small script, or formatter. The runtime must enforce
the declared sandbox policy and report outputs without hiding failures.

## Required Inputs

- `runtime`: Execution runtime or shell.
- `command`: Command or code snippet to run.
- `working_directory`: Directory where execution should happen.
- `sandbox_policy`: Permissions, network access, and filesystem boundaries.

## Expected Outputs

- `stdout`: Captured standard output.
- `stderr`: Captured standard error.
- `exit_code`: Process exit code.
- `artifacts`: Any generated files or paths that matter to the workflow.

## Safety

- Do not run destructive commands unless the workflow explicitly authorizes
  them.
- Keep execution scoped to the declared working directory and sandbox policy.
- Return non-zero exits as structured results rather than suppressing errors.
