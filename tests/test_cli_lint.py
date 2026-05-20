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
