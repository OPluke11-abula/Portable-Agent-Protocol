"""Tests for memory backend behavior."""

from __future__ import annotations

from pathlib import Path

from agent_runtime.memory import JSONFileBackend


def test_json_memory_backend_does_not_create_file_until_write(tmp_path: Path) -> None:
    backend = JSONFileBackend(tmp_path / "memory")

    assert not (tmp_path / "memory" / "memory.json").exists()
    assert backend.read("missing") is None

    backend.write("key", {"value": 1})

    assert backend.read("key") == {"value": 1}
    assert (tmp_path / "memory" / "memory.json").exists()


def test_json_memory_backend_delete_and_clear_do_not_create_file(tmp_path: Path) -> None:
    backend = JSONFileBackend(tmp_path / "memory")

    assert backend.delete("missing") is False
    backend.clear()

    assert not (tmp_path / "memory" / "memory.json").exists()
