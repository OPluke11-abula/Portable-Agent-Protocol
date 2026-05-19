"""Skill execution memory writeback helpers."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _safe_segment(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip()).strip("._")
    return clean or "default"


def write_skill_result(
    skill_name: str,
    params: dict,
    result: dict,
    agent_dir: Path,
    session_id: str,
) -> None:
    """Write a skill execution result to `.agent/memory/<skill>/<session>.md`."""
    agent_path = Path(agent_dir)
    if agent_path.name != ".agent" and (agent_path / ".agent").exists():
        agent_path = agent_path / ".agent"

    safe_skill = _safe_segment(skill_name)
    safe_session = _safe_segment(session_id)
    memory_dir = agent_path / "memory" / safe_skill
    memory_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    content = (
        f"# Skill Result: {safe_skill}\n\n"
        f"- timestamp: {timestamp}\n"
        f"- session_id: {safe_session}\n\n"
        "## Params\n\n"
        "```json\n"
        f"{json.dumps(params, indent=2, ensure_ascii=False)}\n"
        "```\n\n"
        "## Result\n\n"
        "```json\n"
        f"{json.dumps(result, indent=2, ensure_ascii=False)}\n"
        "```\n"
    )
    (memory_dir / f"{safe_session}.md").write_text(content, encoding="utf-8")


def load_skill_memory(skill_name: str, agent_dir: Path, limit: int = 5) -> list[dict]:
    """Load the most recent skill execution records for context."""
    agent_path = Path(agent_dir)
    if agent_path.name != ".agent" and (agent_path / ".agent").exists():
        agent_path = agent_path / ".agent"

    memory_dir = agent_path / "memory" / _safe_segment(skill_name)
    if not memory_dir.exists():
        return []

    records: list[dict[str, Any]] = []
    files = sorted(
        memory_dir.glob("*.md"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in files[: max(limit, 0)]:
        text = path.read_text(encoding="utf-8")
        records.append(
            {
                "path": str(path),
                "session_id": path.stem,
                "content": text,
            }
        )
    return records
