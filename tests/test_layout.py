"""Tests for the declared .agent layout."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from agent_runtime.engine import (
    AgentEngine,
    load_agent_layout,
    load_agent_config,
    validate_agent_config_paths,
)


def _write_agent_md(tmp_path: Path, frontmatter: str) -> Path:
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()
    path = agent_dir / "agent.md"
    content = f"---\n{textwrap.dedent(frontmatter).strip()}\n---\n# body\n"
    path.write_text(content, encoding="utf-8")
    return path


def test_validate_agent_config_paths_accepts_real_repo_layout() -> None:
    config_path = Path(".agent/agent.md")
    config = load_agent_config(config_path)
    validate_agent_config_paths(config, config_path)


def test_load_agent_layout_discovers_real_repo_documents() -> None:
    config_path = Path(".agent/agent.md")
    config = load_agent_config(config_path)
    layout = load_agent_layout(config, config_path)

    assert layout["root"] == Path(".agent")
    assert layout["manifest"] == Path(".agent/agent.md")
    assert layout["entrypoints"]["overview"] == Path(".agent/README.md")
    assert layout["entrypoints"]["skills"] == Path(".agent/skills.md")
    assert layout["directories"]["workflows"] == Path(".agent/workflows")
    assert Path(".agent/workflows/research_and_report.md") in layout[
        "directory_documents"
    ]["workflows"]
    assert Path(".agent/workflows/run_and_explain.md") in layout[
        "directory_documents"
    ]["workflows"]


def test_engine_exposes_declared_layout_metadata() -> None:
    engine = AgentEngine(config_path=".agent/agent.md")

    assert engine.layout["entrypoints"]["prompts"] == Path(".agent/prompts.md")
    assert Path(".agent/prompts/role_template.md") in engine.layout[
        "directory_documents"
    ]["prompts"]


def test_engine_raises_on_missing_declared_layout_path(tmp_path: Path) -> None:
    config_path = _write_agent_md(
        tmp_path,
        """
        name: test-agent
        version: "0.1.0"
        tools:
          - search_web
        protocol:
          entrypoints:
            overview: .agent/README.md
        """,
    )

    with pytest.raises(FileNotFoundError, match="protocol.entrypoints.overview"):
        AgentEngine(config_path=config_path)
