"""Checks for the LAS interop validation plan documentation."""

from __future__ import annotations

from pathlib import Path


def test_las_interop_validation_plan_names_required_components_and_commands() -> None:
    plan = Path("docs/las-interop-validation-plan.md")

    text = plan.read_text(encoding="utf-8")

    for component in (
        "ConductorPlan",
        "LongTermMemoryStore",
        "UnifiedPolicyGate",
        "AuditLedger",
    ):
        assert component in text

    for pap_command in (
        ".\\.venv\\bin\\python.exe -m pytest --no-cov -q",
        ".\\.venv\\bin\\python.exe cli.py lint",
        "git diff --check",
    ):
        assert pap_command in text

    for las_command in (
        "python agent_workspace/pap_validate.py",
        "python agent_workspace/tool_manifest.py validate",
        ".\\scripts\\verify.cmd -SkipViewer",
    ):
        assert las_command in text
