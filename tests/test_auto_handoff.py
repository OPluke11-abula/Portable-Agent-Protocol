"""Tests for Auto Thread-Hopping Trigger (Task 1-08).

Verifies that AgentEngine monitors turn count and context length,
automatically exports a handoff packet when limits are exceeded,
and raises HandoffRequired to signal the host.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_runtime.engine import AgentEngine, HandoffRequired


def _write_workspace(
    tmp_path: Path,
    *,
    max_turns: int = 0,
    max_context_chars: int = 0,
) -> Path:
    """Create a minimal workspace with auto_handoff config."""
    agent_dir = tmp_path / ".agent"
    skills_dir = agent_dir / "skills"
    memory_dir = agent_dir / "memory"
    handoff_dir = memory_dir / "handoff"
    skills_dir.mkdir(parents=True)
    memory_dir.mkdir(parents=True)
    handoff_dir.mkdir(parents=True)
    (skills_dir / "fake_tool.md").write_text("# fake_tool\n", encoding="utf-8")

    auto_handoff_section = ""
    if max_turns or max_context_chars:
        auto_handoff_section = (
            f"auto_handoff:\n"
            f"  max_turns: {max_turns}\n"
            f"  max_context_chars: {max_context_chars}\n"
        )

    config = (
        "---\n"
        'protocol_version: "1.0.0"\n'
        'min_runtime_version: "0.1.0"\n'
        "name: test-agent\n"
        'version: "0.1.0"\n'
        "purpose: Test auto-handoff.\n"
        "language: en-US\n"
        "authorization_level: interactive-approval\n"
        "use_case_tags: [test]\n"
        "tools:\n"
        "  - fake_tool\n"
        "protocol:\n"
        "  root: .agent/\n"
        "  manifest: .agent/agent.md\n"
        "  directories:\n"
        "    skills: .agent/skills/\n"
        "    memory: .agent/memory/\n"
        "memory:\n"
        "  backend: in_memory\n"
        f"{auto_handoff_section}"
        "---\n"
        "\n"
        "# Test Agent\n"
    )
    path = agent_dir / "agent.md"
    path.write_text(config, encoding="utf-8")
    return path


def test_handoff_required_exception_attributes() -> None:
    """Verify HandoffRequired carries the handoff_id and reason."""
    exc = HandoffRequired(handoff_id="abc-123", reason="turn limit exceeded")
    assert exc.handoff_id == "abc-123"
    assert exc.reason == "turn limit exceeded"
    assert "abc-123" in str(exc)
    assert "42" in str(exc)  # exit code reference
    assert HandoffRequired.HANDOFF_EXIT_CODE == 42


def test_no_handoff_when_limits_not_set(tmp_path: Path) -> None:
    """Engine runs normally when auto_handoff is not configured (limits=0)."""
    config_path = _write_workspace(tmp_path, max_turns=0, max_context_chars=0)
    engine = AgentEngine(config_path)
    engine.router.register_tool("fake_tool", lambda params: {"ok": True})

    # Run many times — should never trigger handoff
    for _ in range(100):
        result = engine.run("fake_tool", {"query": "test"})
        assert result == {"ok": True}


def test_turn_count_triggers_handoff(tmp_path: Path) -> None:
    """HandoffRequired is raised when turn count exceeds max_turns."""
    config_path = _write_workspace(tmp_path, max_turns=3)
    engine = AgentEngine(config_path)
    engine.router.register_tool("fake_tool", lambda params: {"ok": True})

    # First 3 turns should succeed
    for i in range(3):
        result = engine.run("fake_tool", {"query": f"turn_{i}"})
        assert result == {"ok": True}

    # 4th turn should trigger handoff
    with pytest.raises(HandoffRequired) as exc_info:
        engine.run("fake_tool", {"query": "overflow"})

    assert "max_turns" in exc_info.value.reason
    assert exc_info.value.handoff_id  # not empty


def test_context_length_triggers_handoff(tmp_path: Path) -> None:
    """HandoffRequired is raised when context chars exceed max_context_chars."""
    config_path = _write_workspace(tmp_path, max_context_chars=100)
    engine = AgentEngine(config_path)
    engine.router.register_tool("fake_tool", lambda params: {"ok": True})

    # First call with small params should work
    engine.run("fake_tool", {"q": "hi"})

    # Second call with large params should trigger
    with pytest.raises(HandoffRequired) as exc_info:
        engine.run("fake_tool", {"q": "x" * 200})

    assert "max_context_chars" in exc_info.value.reason


def test_handoff_export_called_before_exception(tmp_path: Path) -> None:
    """Verify a handoff packet is actually exported before the exception."""
    config_path = _write_workspace(tmp_path, max_turns=1)
    engine = AgentEngine(config_path)
    engine.router.register_tool("fake_tool", lambda params: {"ok": True})

    # First turn succeeds
    engine.run("fake_tool", {"query": "first"})

    # Second turn triggers handoff
    with pytest.raises(HandoffRequired) as exc_info:
        engine.run("fake_tool", {"query": "second"})

    handoff_id = exc_info.value.handoff_id

    # Verify the handoff file was written
    handoff_dir = tmp_path / ".agent" / "memory" / "handoff"
    handoff_file = handoff_dir / f"{handoff_id}.json"
    assert handoff_file.exists(), "Handoff packet file should exist"

    packet = json.loads(handoff_file.read_text(encoding="utf-8"))
    assert "auto-handoff" in packet["task_state"]
    assert "checksum" in packet


def test_configurable_thresholds(tmp_path: Path) -> None:
    """Verify config-driven thresholds are respected."""
    # High limit — should not trigger
    config_path = _write_workspace(tmp_path, max_turns=1000, max_context_chars=1_000_000)
    engine = AgentEngine(config_path)
    engine.router.register_tool("fake_tool", lambda params: {"ok": True})

    for i in range(50):
        result = engine.run("fake_tool", {"query": f"turn_{i}"})
        assert result == {"ok": True}

    assert engine._turn_count == 50
    assert engine._context_chars > 0


def test_turn_count_resets_on_new_engine(tmp_path: Path) -> None:
    """Each engine instance starts with fresh counters."""
    config_path = _write_workspace(tmp_path, max_turns=2)

    engine1 = AgentEngine(config_path)
    engine1.router.register_tool("fake_tool", lambda params: {"ok": True})
    engine1.run("fake_tool", {"q": "a"})
    engine1.run("fake_tool", {"q": "b"})
    assert engine1._turn_count == 2

    # New engine should start fresh
    engine2 = AgentEngine(config_path)
    assert engine2._turn_count == 0
    assert engine2._context_chars == 0
