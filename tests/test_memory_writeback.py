"""Tests for skill execution memory writeback helpers."""

from __future__ import annotations

from pathlib import Path

from agent_runtime.memory.writeback import load_skill_memory, write_skill_result


def test_write_skill_result_sanitizes_path_segments_and_loads_recent_records(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    agent_dir = workspace / ".agent"
    agent_dir.mkdir(parents=True)

    write_skill_result(
        "search/web skill",
        {"query": "Portable Agent"},
        {"ok": True},
        workspace,
        "session 01/unsafe",
    )

    records = load_skill_memory("search/web skill", workspace)

    assert len(records) == 1
    assert records[0]["session_id"] == "session_01_unsafe"
    assert "Skill Result: search_web_skill" in records[0]["content"]
    assert '"query": "Portable Agent"' in records[0]["content"]
    assert '"ok": true' in records[0]["content"]
    assert Path(records[0]["path"]).exists()


def test_load_skill_memory_handles_missing_directory_and_limit(tmp_path: Path) -> None:
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    assert load_skill_memory("missing", agent_dir) == []

    for index in range(3):
        write_skill_result(
            "code executor",
            {"index": index},
            {"result": index},
            agent_dir,
            f"session-{index}",
        )

    assert load_skill_memory("code executor", agent_dir, limit=0) == []
    latest_two = load_skill_memory("code executor", agent_dir, limit=2)
    assert len(latest_two) == 2
