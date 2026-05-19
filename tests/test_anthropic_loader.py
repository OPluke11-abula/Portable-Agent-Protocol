"""Tests for Anthropic skills loading and PAP registry sync."""

from __future__ import annotations

from pathlib import Path

from agent_runtime.loaders import anthropic_skills_loader as loader
from agent_runtime.loaders.anthropic_skills_loader import (
    SkillRecord,
    load_from_github,
    load_from_local,
    sync_to_registry,
)


def test_load_from_local_reads_skill_records(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "search-web"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: search-web\n"
        "description: Search web sources.\n"
        "---\n\n"
        "# Search Web\n",
        encoding="utf-8",
    )

    records = load_from_local(tmp_path / "skills")

    assert records == [
        SkillRecord(
            name="search_web",
            description="Search web sources.",
            source="anthropic",
            source_path=str(skill_dir / "SKILL.md"),
            anthropic_compatible=True,
            pap_contract_path=None,
        )
    ]


def test_sync_to_registry_preserves_local_pap_and_adds_anthropic(tmp_path: Path) -> None:
    agent_dir = tmp_path / ".agent"
    (agent_dir / "skills").mkdir(parents=True)
    (agent_dir / "skills" / "search_web.md").write_text("# Skill: search_web\n", encoding="utf-8")

    sync_to_registry(
        [
            SkillRecord(
                name="code_review",
                description="Review code.",
                source="anthropic",
                source_path="https://example.test/code-review/SKILL.md",
                anthropic_compatible=True,
                pap_contract_path=None,
            )
        ],
        agent_dir,
    )

    registry = (agent_dir / "skills.md").read_text(encoding="utf-8")

    assert "name: search_web" in registry
    assert "source: pap" in registry
    assert "name: code_review" in registry
    assert "source: anthropic" in registry


def test_load_from_github_uses_tree_and_raw_content(monkeypatch) -> None:
    def fake_fetch_json(url: str) -> dict:
        assert "github.com/repos/anthropics/skills" in url
        return {"tree": [{"type": "blob", "path": "skills/search-web/SKILL.md"}]}

    def fake_fetch_text(url: str) -> str:
        assert "raw.githubusercontent.com/anthropics/skills/main/skills/search-web/SKILL.md" in url
        return "---\nname: search-web\ndescription: Search web.\n---\n# Search Web\n"

    monkeypatch.setattr(loader, "_fetch_json", fake_fetch_json)
    monkeypatch.setattr(loader, "_fetch_text", fake_fetch_text)

    records = load_from_github()

    assert len(records) == 1
    assert records[0].name == "search_web"
    assert records[0].source == "anthropic"
