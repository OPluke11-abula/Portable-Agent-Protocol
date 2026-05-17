# PAP Conformance Test Suite

This directory contains the language-agnostic conformance tests for the Portable Agent Protocol.

Any runtime implementation (e.g., Python `agent_runtime`, TypeScript `pap-runtime-ts`, Go, Rust) that wishes to be certified as **PAP-Compatible** must implement a test runner that executes and passes these test cases.

## Test Format

Tests are defined as YAML files. Each file groups tests by a specific domain (e.g., schema validation, layout resolution).

A typical test case provides:
1. `name`: The name of the test.
2. `input`: A mock file system structure or an inline YAML payload to parse.
3. `expected_behavior`: What the runtime must do (e.g., `accept`, `reject_with_error`).
