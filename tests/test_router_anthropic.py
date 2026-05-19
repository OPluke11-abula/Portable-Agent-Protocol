"""Tests for Anthropic-aware routing and skill memory writeback."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from pathlib import Path

from agent_runtime.memory.writeback import load_skill_memory, write_skill_result
from agent_runtime.router import Router


def test_writeback_round_trip_loads_recent_records(tmp_path: Path) -> None:
    agent_dir = tmp_path / ".agent"

    write_skill_result(
        "search_web",
        {"query": "test"},
        {"summary": "ok"},
        agent_dir,
        "session-1",
    )

    records = load_skill_memory("search_web", agent_dir)

    assert len(records) == 1
    assert records[0]["session_id"] == "session-1"
    assert '"query": "test"' in records[0]["content"]
    assert '"summary": "ok"' in records[0]["content"]


def test_dispatch_via_claude_api_loads_and_writes_memory(tmp_path: Path, monkeypatch) -> None:
    agent_dir = tmp_path / ".agent"
    skills_dir = agent_dir / "skills"
    skills_dir.mkdir(parents=True)
    skill_path = skills_dir / "search_web.md"
    skill_path.write_text("# Skill: search_web\n\nSearch web sources.\n", encoding="utf-8")

    router = Router()

    def fake_call(prompt: str, skill_ref=None) -> dict:
        assert "Search web sources." in prompt
        assert "recent_skill_memory" in prompt
        assert skill_ref["skill_id"] == "skill_123"
        return {"via": "claude_api", "content": "done", "skill_ref": skill_ref}

    monkeypatch.setattr(router, "_call_claude_api", fake_call)

    result = router.dispatch_via_claude_api(
        "search_web",
        {
            "query": "pytest",
            "session_id": "session-2",
            "anthropic_skill_id": "skill_123",
            "anthropic_skill_type": "custom",
        },
        skill_path,
    )

    assert result["content"] == "done"
    assert result["skill_ref"] == {
        "type": "custom",
        "skill_id": "skill_123",
        "version": "latest",
    }
    records = load_skill_memory("search_web", agent_dir)
    assert len(records) == 1
    assert records[0]["session_id"] == "session-2"


def test_resolve_anthropic_builtin_skill_ref() -> None:
    router = Router()

    assert router._resolve_anthropic_skill_ref("xlsx", {}) == {
        "type": "anthropic",
        "skill_id": "xlsx",
        "version": "latest",
    }


def test_call_claude_api_uses_container_skills(monkeypatch) -> None:
    captured = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                content=[SimpleNamespace(text="ok")],
                model=kwargs["model"],
            )

    class FakeAnthropic:
        def __init__(self, api_key: str) -> None:
            assert api_key == "test-key"
            self.beta = SimpleNamespace(messages=FakeMessages())
            self.messages = FakeMessages()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropic))

    router = Router()
    result = router._call_claude_api(
        "prompt",
        skill_ref={"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
    )

    assert captured["container"] == {
        "skills": [{"type": "anthropic", "skill_id": "xlsx", "version": "latest"}]
    }
    assert captured["betas"] == ["code-execution-2025-08-25", "skills-2025-10-02"]
    assert captured["tools"] == [{"type": "code_execution_20250825", "name": "code_execution"}]
    assert result["content"] == "ok"
