# Portable Agent Protocol (PAP) — Dependency & Runtime Requirements Specification

This document details the minimal dependency architecture, optional package fallbacks, and standard library alignment of the Portable Agent Protocol (PAP) reference runtime.

---

## 🏛️ 1. Core Philosophy: Standard Library First

To maximize portability, lightweight integration, and cross-platform compatibility, the PAP reference runtime is designed with a **Standard Library First** architectural style:
1. **Stateless Logic**: Core routing, tool dispatching, execution layout mapping, and in-memory key-value state management rely exclusively on built-in standard Python modules.
2. **Minimal Dependencies**: The core runtime holds zero hard dependencies on large third-party runtime frameworks (such as Pydantic, FastAPI, or Pydantic-Settings).
3. **Robust Isolation**: The declarative agent workspace specification (`.agent/`) is fully decoupled from the runtime implementation, allowing other languages (TypeScript, Go, Rust) to instantiate PAP without package-bloat.

---

## 📦 2. Dependency Audit & Justification

The project's dependency surface in `pyproject.toml` is partitioned strictly between **Core Runtime** and **Optional Developer / Validation** environments:

### Core Runtime Dependencies (`[project] dependencies`)

| Package | Version | Requirement Justification |
| :--- | :--- | :--- |
| **`PyYAML`** | `>= 6.0` | **Mandatory**. The PAP three-tier model relies on parsing declarative YAML front-matters embedded at the top of markdown documents (`agent.md`, `.agent/skills/*.md`, `.agent/workflows/*.md`). PyYAML is used strictly to safely ingest these declarative structures. |

### Optional Developer / Validation Dependencies (`[project.optional-dependencies] dev`)

| Package | Version | Requirement Justification |
| :--- | :--- | :--- |
| **`jsonschema`** | `*` | **Optional**. Used strictly at boundary initialization (bootstrap validation of `agent.md`, skill contracts, and workflow step shapes). If absent, the engine gracefully falls back to basic structural validations without throwing errors or crashing. |
| **`pytest`** | `*` | Test harness for executing standard verification blocks. |
| **`pytest-cov`** | `*` | Test coverage enforcer (requiring a minimum of 80% coverage). |
| **`ruff`** | `*` | High-performance static code style checker. |
| **`mypy`** | `*` | Strict static type checker for type-safety assurance. |

---

## 🛡️ 3. Zero-Dependency Optional Fallbacks

When `jsonschema` is not present in the execution environment, the reference runtime modules implement resilient fallback procedures:

### A. Agent Engine Bootstrapping (`agent_runtime/engine.py`)
- The import of `jsonschema` is wrapped inside a safe `try-except ImportError` block.
- During bootstrapping or manual validation (`validate_agent_schema()`), if `jsonschema` is `None`, the runtime skips the schema validation layer and emits a clean warning:
  ```
  [WARNING] jsonschema is not installed. Schema validation skipped.
  ```
- Gracefully permits agent startup and task runs even in micro-environments without dependencies.

### B. Skill Router and Dispatching (`agent_runtime/router.py`)
- The router functions completely independently of any schema validation package.
- Input formats and skill IDs are verified using regex and type safety patterns (`validate_skill_id()`), guaranteeing zero vulnerability to injection or traversal without external dependency requirements.

### C. Multi-Account Persistent Auditor (`agent_runtime/account_manager.py`)
- If `jsonschema` is absent, `AccountManager.validate_data()` automatically falls back to manual dictionary verification, asserting exact types and required key fields to ensure system integrity.

### D. Prompt Composer Variable Scans (`agent_runtime/prompt_composer.py`)
- Standard variable escaping (`escape_prompt_value()`) and role instruction parsing bypass external schema validation when the module is not loaded.
