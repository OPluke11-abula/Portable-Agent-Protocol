"""Tests for PAP <-> Anthropic skill format conversion."""

from __future__ import annotations

from pathlib import Path

from agent_runtime.bridges.anthropic_skill_bridge import (
    anthropic_to_pap,
    export_all_skills,
    pap_to_anthropic,
)


def test_pap_to_anthropic_exports_frontmatter(tmp_path: Path) -> None:
    pap_skill = tmp_path / "search_web.md"
    pap_skill.write_text(
        "# Skill: search_web\n\n"
        "Search trusted web sources and return cited summaries.\n\n"
        "## Required Inputs\n\n- query\n",
        encoding="utf-8",
    )

    exported = pap_to_anthropic(pap_skill)

    assert exported.startswith("---\n")
    assert 'name: "search-web"' in exported
    assert 'description: "Search trusted web sources and return cited summaries."' in exported
    assert "# Search Web Skill" in exported
    assert "## PAP Contract" in exported


def test_anthropic_to_pap_preserves_metadata_and_body(tmp_path: Path) -> None:
    skill_dir = tmp_path / "code-review"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        "---\n"
        'name: "code-review"\n'
        'description: "Review code for defects."\n'
        "---\n\n"
        "# Code Review\n\nCheck behavior, tests, and regressions.\n",
        encoding="utf-8",
    )

    pap = anthropic_to_pap(skill_md)

    assert pap.startswith("# Skill: code_review")
    assert "Review code for defects." in pap
    assert "- source: anthropic" in pap
    assert "Check behavior, tests, and regressions." in pap


def test_export_all_skills_writes_skill_md_folders(tmp_path: Path) -> None:
    agent_dir = tmp_path / ".agent"
    skills_dir = agent_dir / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "search_web.md").write_text(
        "# Skill: search_web\n\nSearch web sources.\n", encoding="utf-8"
    )
    (skills_dir / "_template.md").write_text("# Template\n", encoding="utf-8")

    exported = export_all_skills(agent_dir, tmp_path / "anthropic_skills")

    assert exported == [tmp_path / "anthropic_skills" / "search-web" / "SKILL.md"]
    assert exported[0].exists()
    assert 'name: "search-web"' in exported[0].read_text(encoding="utf-8")
