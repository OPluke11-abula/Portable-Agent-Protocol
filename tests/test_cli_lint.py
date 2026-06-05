"""Tests for the workspace linter CLI command in cli.py and agent_runtime/lint.py."""

from __future__ import annotations

import re
from pathlib import Path
import pytest
import yaml

from cli import main
from agent_runtime.lint import WorkspaceLinter


def _setup_spec_schemas(tmp_path: Path) -> None:
    """Helper to copy original schemas to temp path spec/ for validation testing."""
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir(exist_ok=True)
    original_root = Path(__file__).parent.parent
    for schema_file in original_root.glob("spec/*.json"):
        content = schema_file.read_text(encoding="utf-8")
        (spec_dir / schema_file.name).write_text(content, encoding="utf-8")


def test_cli_lint_valid_scaffold(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    _setup_spec_schemas(tmp_path)

    # 1. Initialize a clean workspace
    exit_init = main(["init", "--project-name", "proj", "--agent-name", "agent", "--skills", "search_web"])
    assert exit_init == 0

    # 2. Run lint
    exit_lint = main(["--config", str(tmp_path / ".agent" / "agent.md"), "lint"])
    assert exit_lint == 0


def test_cli_lint_version_fixes(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    _setup_spec_schemas(tmp_path)

    # Initialize a clean workspace
    exit_init = main(["init", "--project-name", "proj", "--agent-name", "agent"])
    assert exit_init == 0

    agent_md = tmp_path / ".agent" / "agent.md"
    content = agent_md.read_text(encoding="utf-8")

    # Mangle the version fields to be non-semver
    content = content.replace('version: "0.1.0"', 'version: "invalid-version"')
    agent_md.write_text(content, encoding="utf-8")

    # Run lint - should return 1 because there is an error
    exit_lint = main(["--config", str(agent_md), "lint"])
    assert exit_lint == 1

    # Run lint with --fix
    exit_fix = main(["--config", str(agent_md), "lint", "--fix"])
    assert exit_fix == 0  # All issues resolved successfully, returns 0

    # Check if version was cleaned/fixed to "0.0.0" or similar semver
    content_fixed = agent_md.read_text(encoding="utf-8")
    assert 'version: 0.0.0' in content_fixed or 'version: "0.0.0"' in content_fixed or 'version: 0.1.0' in content_fixed


def test_cli_lint_missing_and_unregistered_skills(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    _setup_spec_schemas(tmp_path)

    # Initialize workspace with no skills pre-installed
    exit_init = main(["init", "--project-name", "proj", "--agent-name", "agent"])
    assert exit_init == 0

    agent_md = tmp_path / ".agent" / "agent.md"

    # Add a declared tool that doesn't exist
    content = agent_md.read_text(encoding="utf-8")
    # Insert tool 'missing_tool' in tools array
    content = content.replace("tools: []", "tools:\n  - missing_tool")
    agent_md.write_text(content, encoding="utf-8")

    # Verify lint detects the missing skill contract file
    linter = WorkspaceLinter(agent_md)
    issues = linter.run_all_checks()
    assert any(i.severity == "error" and "missing_tool" in i.message for i in issues)

    # Apply fixes to generate the missing contract
    fixed_count = linter.apply_fixes()
    assert fixed_count == 1
    assert (tmp_path / ".agent" / "skills" / "missing_tool.md").is_file()

    # Now create an unregistered skill file
    unreg_file = tmp_path / ".agent" / "skills" / "unregistered_tool.md"
    unreg_content = """---
id: "unregistered_tool"
name: "unregistered_tool"
description: "some tool"
version: "1.0.0"
inputs: {}
outputs: {}
safety_notes: []
---
"""
    unreg_file.write_text(unreg_content, encoding="utf-8")

    # Verify lint detects the unregistered skill
    issues = linter.run_all_checks()
    assert any(i.severity == "warning" and "unregistered_tool" in i.message for i in issues)

    # Apply fixes to register the tool in agent.md
    fixed_count = linter.apply_fixes()
    assert fixed_count == 1
    content_after = agent_md.read_text(encoding="utf-8")
    assert "- unregistered_tool" in content_after


def test_cli_lint_workflow_dag(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    _setup_spec_schemas(tmp_path)

    # Scaffold clean workspace
    exit_init = main(["init", "--project-name", "proj", "--agent-name", "agent"])
    assert exit_init == 0

    workflows_dir = tmp_path / ".agent" / "workflows"
    workflows_dir.mkdir(exist_ok=True)

    # 1. Circular Dependency
    circle_file = workflows_dir / "circle.md"
    circle_file.write_text("""---
name: "circle"
steps:
  - id: stepA
    tool: search_web
    depends_on: [stepB]
  - id: stepB
    tool: query_db
    depends_on: [stepA]
---
""", encoding="utf-8")

    linter = WorkspaceLinter(tmp_path / ".agent" / "agent.md")
    issues = linter.run_all_checks()
    assert any("Circular dependency detected" in i.message for i in issues)

    # Clean circular file
    circle_file.unlink()

    # 2. Broken Step Dependency (depends on non-existent step)
    broken_file = workflows_dir / "broken.md"
    broken_file.write_text("""---
name: "broken"
steps:
  - id: stepA
    tool: search_web
    depends_on: [non_existent_step]
---
""", encoding="utf-8")

    issues = linter.run_all_checks()
    assert any("depends on non-existent step" in i.message for i in issues)

    broken_file.unlink()

    # 3. Missing declared dependency for parameter reference
    missing_dep_file = workflows_dir / "missing_dep.md"
    missing_dep_file.write_text("""---
name: "missing_dep"
steps:
  - id: stepA
    tool: search_web
    params:
      query: "hello"
  - id: stepB
    tool: query_db
    params:
      query: "{{steps.stepA.outputs.result}}"
---
""", encoding="utf-8")

    issues = linter.run_all_checks()
    assert any("does not declare a dependency on it" in i.message for i in issues)


def test_cli_lint_decoupling_knowledge_base(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    _setup_spec_schemas(tmp_path)

    exit_init = main(["init", "--project-name", "proj", "--agent-name", "agent"])
    assert exit_init == 0

    agent_md = tmp_path / ".agent" / "agent.md"
    kb_dir = tmp_path / ".agent" / "knowledge_base"

    # 1. Test executable file inside knowledge base
    bad_file = kb_dir / "script.py"
    bad_file.write_text("print('hello')", encoding="utf-8")

    linter = WorkspaceLinter(agent_md)
    issues = linter.run_all_checks()
    assert any("Decoupling violation: Non-declarative/executable file" in i.message for i in issues)
    bad_file.unlink()

    # 2. Test implementation code blocks in markdown file inside knowledge base
    impl_md = kb_dir / "impl.md"
    # Create a >45 line code block to trigger the decoupling check
    python_code_lines = ["import sys", "def run():"] + [f"    print({i})" for i in range(50)]
    python_block = "\n".join(python_code_lines)
    impl_md.write_text(f"""---
id: impl
title: "Implementation"
tags: []
created: "2026-05-24"
updated: "2026-05-24"
---
Here is some implementation details:
```python
{python_block}
```
""", encoding="utf-8")

    issues = linter.run_all_checks()
    assert any("Decoupling violation: Knowledge base entry contains a full/large implementation code block" in i.message for i in issues)
    impl_md.unlink()


def test_cli_lint_decoupling_skills(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    _setup_spec_schemas(tmp_path)

    exit_init = main(["init", "--project-name", "proj", "--agent-name", "agent"])
    assert exit_init == 0

    agent_md = tmp_path / ".agent" / "agent.md"
    skills_dir = tmp_path / ".agent" / "skills"

    # 1. Test non-markdown file inside skills directory
    bad_file = skills_dir / "helper.py"
    bad_file.write_text("def x(): pass", encoding="utf-8")

    linter = WorkspaceLinter(agent_md)
    issues = linter.run_all_checks()
    assert any("Decoupling violation: Non-markdown file 'helper.py' found in skills directory." in i.message for i in issues)
    bad_file.unlink()

    # 2. Test implementation code blocks in skill contract
    skill_md = skills_dir / "dummy.md"
    js_code_lines = ["const x = 5;", "function hello() {"] + [f"    console.log({i});" for i in range(50)] + ["}"]
    js_block = "\n".join(js_code_lines)
    skill_md.write_text(f"""---
id: "dummy"
name: "dummy"
description: "dummy description"
version: "1.0.0"
inputs: {{}}
outputs: {{}}
safety_notes: []
---
# dummy
```js
{js_block}
```
""", encoding="utf-8")

    issues = linter.run_all_checks()
    assert any("Decoupling violation: Skill contract contains a full/large implementation code block" in i.message for i in issues)
    skill_md.unlink()


def test_cli_lint_decoupling_tools(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    _setup_spec_schemas(tmp_path)

    exit_init = main(["init", "--project-name", "proj", "--agent-name", "agent"])
    assert exit_init == 0

    agent_md = tmp_path / ".agent" / "agent.md"

    # Create dummy tools dir under project root / agent_runtime / tools
    tools_dir = tmp_path / "agent_runtime" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    # 1. Test non-python file in tools
    bad_file = tools_dir / "notes.txt"
    bad_file.write_text("hello", encoding="utf-8")

    linter = WorkspaceLinter(agent_md)
    issues = linter.run_all_checks()
    assert any("Decoupling violation: Non-python file 'notes.txt' found in runtime tools directory." in i.message for i in issues)
    bad_file.unlink()

    # 2. Test mutable module-level state
    mutable_tool = tools_dir / "mutable_tool.py"
    mutable_tool.write_text("""
my_cache = []
def run():
    pass
""", encoding="utf-8")

    issues = linter.run_all_checks()
    assert any("Decoupling violation: Tool contains mutable module-level state 'my_cache'." in i.message for i in issues)
    mutable_tool.unlink()

    # 3. Test global statement
    global_tool = tools_dir / "global_tool.py"
    global_tool.write_text("""
def run():
    global x
    x = 5
""", encoding="utf-8")

    issues = linter.run_all_checks()
    assert any("Decoupling violation: Tool contains stateful 'global' statement." in i.message for i in issues)
    global_tool.unlink()

    # 4. Test potential hardcoded credentials
    secret_tool = tools_dir / "secret_tool.py"
    secret_tool.write_text("""
API_KEY = "sk-live-1234abcd5678"
def run():
    pass
""", encoding="utf-8")

    issues = linter.run_all_checks()
    assert any("Potential hardcoded credential or secret in 'API_KEY'" in i.message for i in issues)
    secret_tool.unlink()

