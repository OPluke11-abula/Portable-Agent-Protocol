# Contributing to Portable Agent Protocol (PAP)

Thank you for your interest in contributing to the Portable Agent Protocol (PAP)! This repository contains both the declarative agent workspace specifications (`.agent/`) and the reference Python runtime (`agent_runtime/`).

This guide outlines our development standards, contribution workflows, and validation procedures.

---

## 🗺️ 1. Codebase Architecture

Contributions generally fall into one of two categories:

### A. Skill Contracts (`.agent/skills/`)
Skill contracts represent the capabilities exposed to the agent. They are defined as Markdown files with YAML front-matter conforming strictly to `spec/skill-contract.schema.json`.
- **Location**: `.agent/skills/<skill_id>.md`
- **Requirements**:
  - Must declare precise JSON types for all inputs and outputs: `["string", "integer", "boolean", "number", "float", "array", "object"]`.
  - Must document safety notes and descriptions.
  - Implementation tool modules (if executing locally) belong in `agent_runtime/tools/<tool_name>.py` and must be stateless (no global mutable variables, no `global` statements).

### B. Reference Runtime (`agent_runtime/`)
The Python runtime boots the agent workspace, validates configurations, manages memory states, executes DAG workflows, and audits LLM usage.
- **Rules**:
  - Keep core engine dependencies minimal. Core runtime modules must rely on Python's standard library and `PyYAML`.
  - Any optional library (like `jsonschema`) must be imported inside `try-except ImportError` blocks with graceful fallbacks.

---

## 🛠️ 2. Development Setup

Follow these steps to set up a clean, local development environment:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/OPluke11-abula/Portable-Agent-Protocol.git
   cd Portable-Agent-Protocol
   ```

2. **Install with Developer Tools**:
   Install the package in editable mode with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

---

## 🚦 3. Code Standards & Static Checks

Before submitting a Pull Request, all changes must pass our local validation tools:

### A. Workspace Linter (`cli.py lint`)
Checks markdown front-matters, workflow DAG validity, and "Brain & Hands" decoupling rules:
```bash
python cli.py lint
```
*Note: Large implementation blocks or executable code inside `.agent/skills/` or `.agent/knowledge_base/` are strictly blocked by the linter.*

### B. Schema Validator (`cli.py validate`)
Verifies that all workspace configurations comply with the declarative JSON schemas under `spec/`:
```bash
python cli.py validate
```

### C. Formatting and Style
We use standard linting tools to check formatting:
- Runs static formatting scans: `ruff check .`
- Type checking verification: `mypy .`

---

## 🧪 4. Testing & Code Coverage

We require all additions to be fully covered by automated unit and integration tests.

- **Running Tests**:
  ```bash
  python -m pytest
  ```
- **Coverage Goal**:
  Overall code coverage must remain **above 80%**. The test runner will automatically fail if the coverage drops below this threshold.
- **Isolated Tests**:
  If debugging a specific test file, you can pass `--no-cov` to bypass coverage checks:
  ```bash
  python -m pytest tests/test_performance.py --no-cov
  ```

---

## 🚀 5. Submission Checklist

1. Make sure all code is fully tested.
2. Run `python cli.py lint` and `python cli.py validate` to ensure 100% compliance.
3. Keep the git commit history clean and use semantic commit messages (e.g. `feat: ...`, `fix: ...`, `docs: ...`).
