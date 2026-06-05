"""Tests for the KnowledgeBase module (Phase 1-02).

Validates retrieval, full-text querying, index listing, schema conformance
of front-matter, and strict read-only protection.
"""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_kb_dir(tmp_path: Path) -> Path:
    """Create a minimal knowledge_base directory with two entries."""
    kb_dir = tmp_path / ".agent" / "knowledge_base"
    kb_dir.mkdir(parents=True, exist_ok=True)

    (kb_dir / "api_docs.md").write_text(
        textwrap.dedent("""\
        ---
        id: api-docs
        title: API Documentation Portal
        tags: [api, documentation, reference]
        created: "2026-05-20"
        updated: "2026-05-20"
        ---

        # API Docs Placeholder

        本檔案代表可檢索的 API 文件入口。
        """),
        encoding="utf-8",
    )

    (kb_dir / "system_architecture.md").write_text(
        textwrap.dedent("""\
        ---
        id: system-architecture
        title: System Architecture Portal
        tags: [architecture, topology, design]
        created: "2026-05-20"
        updated: "2026-05-20"
        ---

        # System Architecture Placeholder

        本檔案代表系統架構知識入口。

        模組邊界、資料流、事件流、技術決策摘要
        """),
        encoding="utf-8",
    )

    # index.json
    index = [
        {
            "id": "api-docs",
            "title": "API Documentation Portal",
            "path": str(kb_dir / "api_docs.md"),
            "tags": ["api", "documentation", "reference"],
            "created": "2026-05-20",
            "updated": "2026-05-20",
        },
        {
            "id": "system-architecture",
            "title": "System Architecture Portal",
            "path": str(kb_dir / "system_architecture.md"),
            "tags": ["architecture", "topology", "design"],
            "created": "2026-05-20",
            "updated": "2026-05-20",
        },
    ]
    (kb_dir / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

    return kb_dir


def _build_knowledge_base(tmp_path: Path):
    """Build a KnowledgeBase backed by a temporary directory."""
    from agent_runtime.knowledge import KnowledgeBase

    kb_dir = _make_kb_dir(tmp_path)

    # Build a minimal mock engine
    engine = MagicMock()
    engine.config_path = tmp_path / ".agent" / "agent.md"
    engine.layout = {"directories": {"knowledge_base": kb_dir}}

    return KnowledgeBase(engine)


# ---------------------------------------------------------------------------
# Tests: Retrieval
# ---------------------------------------------------------------------------

class TestKnowledgeBaseGet:
    def test_get_existing_entry(self, tmp_path: Path) -> None:
        kb = _build_knowledge_base(tmp_path)
        entry = kb.get("api-docs")
        assert entry is not None
        assert entry["id"] == "api-docs"
        assert entry["title"] == "API Documentation Portal"
        assert "tags" in entry
        assert "content" in entry
        assert "API Docs Placeholder" in entry["content"]

    def test_get_second_entry(self, tmp_path: Path) -> None:
        kb = _build_knowledge_base(tmp_path)
        entry = kb.get("system-architecture")
        assert entry is not None
        assert entry["id"] == "system-architecture"
        assert "architecture" in entry["tags"]

    def test_get_nonexistent_returns_none(self, tmp_path: Path) -> None:
        kb = _build_knowledge_base(tmp_path)
        assert kb.get("does-not-exist") is None


# ---------------------------------------------------------------------------
# Tests: Query
# ---------------------------------------------------------------------------

class TestKnowledgeBaseQuery:
    def test_query_by_title(self, tmp_path: Path) -> None:
        kb = _build_knowledge_base(tmp_path)
        results = kb.query("API")
        assert len(results) >= 1
        ids = [r["id"] for r in results]
        assert "api-docs" in ids

    def test_query_by_tag(self, tmp_path: Path) -> None:
        kb = _build_knowledge_base(tmp_path)
        results = kb.query("topology")
        assert len(results) >= 1
        ids = [r["id"] for r in results]
        assert "system-architecture" in ids

    def test_query_by_body_content(self, tmp_path: Path) -> None:
        kb = _build_knowledge_base(tmp_path)
        results = kb.query("模組邊界")
        assert len(results) >= 1
        ids = [r["id"] for r in results]
        assert "system-architecture" in ids

    def test_query_case_insensitive(self, tmp_path: Path) -> None:
        kb = _build_knowledge_base(tmp_path)
        results_lower = kb.query("api")
        results_upper = kb.query("API")
        assert len(results_lower) == len(results_upper)

    def test_query_no_match(self, tmp_path: Path) -> None:
        kb = _build_knowledge_base(tmp_path)
        results = kb.query("nonexistent_keyword_xyz")
        assert results == []


# ---------------------------------------------------------------------------
# Tests: List
# ---------------------------------------------------------------------------

class TestKnowledgeBaseList:
    def test_list_entries(self, tmp_path: Path) -> None:
        kb = _build_knowledge_base(tmp_path)
        entries = kb.list_entries()
        assert len(entries) == 2
        ids = {e["id"] for e in entries}
        assert ids == {"api-docs", "system-architecture"}


# ---------------------------------------------------------------------------
# Tests: Write Protection
# ---------------------------------------------------------------------------

class TestKnowledgeBaseWriteProtection:
    def test_write_raises_permission_error(self, tmp_path: Path) -> None:
        kb = _build_knowledge_base(tmp_path)
        with pytest.raises(PermissionError, match="T-04 Protocol Evolution"):
            kb.write("api-docs", {"data": "test"})

    def test_update_raises_permission_error(self, tmp_path: Path) -> None:
        kb = _build_knowledge_base(tmp_path)
        with pytest.raises(PermissionError, match="T-04 Protocol Evolution"):
            kb.update("api-docs", {"data": "test"})

    def test_delete_raises_permission_error(self, tmp_path: Path) -> None:
        kb = _build_knowledge_base(tmp_path)
        with pytest.raises(PermissionError, match="T-04 Protocol Evolution"):
            kb.delete("api-docs")


# ---------------------------------------------------------------------------
# Tests: Edge Cases
# ---------------------------------------------------------------------------

class TestKnowledgeBaseEdgeCases:
    def test_missing_index_json(self, tmp_path: Path) -> None:
        """KnowledgeBase should gracefully handle missing index.json."""
        from agent_runtime.knowledge import KnowledgeBase

        kb_dir = tmp_path / ".agent" / "knowledge_base"
        kb_dir.mkdir(parents=True, exist_ok=True)

        engine = MagicMock()
        engine.config_path = tmp_path / ".agent" / "agent.md"
        engine.layout = {"directories": {"knowledge_base": kb_dir}}

        kb = KnowledgeBase(engine)
        assert kb.list_entries() == []
        assert kb.query("anything") == []

    def test_malformed_frontmatter(self, tmp_path: Path) -> None:
        """Entries without valid front-matter should be silently skipped."""
        from agent_runtime.knowledge import KnowledgeBase

        kb_dir = tmp_path / ".agent" / "knowledge_base"
        kb_dir.mkdir(parents=True, exist_ok=True)

        # File with no front-matter
        (kb_dir / "bad.md").write_text("# No front matter here\n", encoding="utf-8")

        index = [{"id": "bad", "title": "Bad Entry", "path": str(kb_dir / "bad.md"), "tags": ["test"], "created": "2026-01-01", "updated": "2026-01-01"}]
        (kb_dir / "index.json").write_text(json.dumps(index), encoding="utf-8")

        engine = MagicMock()
        engine.config_path = tmp_path / ".agent" / "agent.md"
        engine.layout = {"directories": {"knowledge_base": kb_dir}}

        kb = KnowledgeBase(engine)
        assert kb.get("bad") is None

    def test_get_with_missing_file(self, tmp_path: Path) -> None:
        """If the indexed file doesn't exist on disk, get() returns None."""
        from agent_runtime.knowledge import KnowledgeBase

        kb_dir = tmp_path / ".agent" / "knowledge_base"
        kb_dir.mkdir(parents=True, exist_ok=True)

        index = [{"id": "ghost", "title": "Ghost", "path": str(kb_dir / "ghost.md"), "tags": ["phantom"], "created": "2026-01-01", "updated": "2026-01-01"}]
        (kb_dir / "index.json").write_text(json.dumps(index), encoding="utf-8")

        engine = MagicMock()
        engine.config_path = tmp_path / ".agent" / "agent.md"
        engine.layout = {"directories": {"knowledge_base": kb_dir}}

        kb = KnowledgeBase(engine)
        assert kb.get("ghost") is None


# ---------------------------------------------------------------------------
# Tests: Task 5-02 Knowledge Base Auto-Update Lifecycle
# ---------------------------------------------------------------------------

class TestKnowledgeBaseAutoUpdate:
    def test_heuristics_classification(self) -> None:
        from agent_runtime.knowledge import extract_knowledge_heuristics

        # 1. Low-value short content
        assert extract_knowledge_heuristics("short content") is None

        # 2. High-value content: Solved bug
        bug_content = (
            "SQLite database tool threw a critical runtime exception. "
            "The error occurred because of a thread safety collision. We resolved the bug by "
            "introducing a process-level threading lock around the database execution block, "
            "ensuring thread serialization and preventing future deadlocks."
        )
        res = extract_knowledge_heuristics(bug_content)
        assert res is not None
        assert "bug-fix" in res["tags"]
        assert "SQLite" in res["title"]

        # 3. High-value content: Best practice resolution
        pattern_content = (
            "This document establishes a successful pattern for multi-agent handoffs. "
            "To prevent context token overflow, the agent must check current token counts "
            "and execute a handoff checklist whenever turns exceed 15. This best practice "
            "ensures continuous context window optimization and clean pipeline checkpoints."
        )
        res = extract_knowledge_heuristics(pattern_content)
        assert res is not None
        assert "best-practice" in res["tags"]

        # 4. Detailed successful content without specific keywords
        detailed_success = (
            "The execution of the overall migration was successful and clean. We completed the file structural "
            "checks, verified all layout directories exist, compiled the latest schemas, and finished "
            "the deployment check without warnings in the staging area."
        )
        res = extract_knowledge_heuristics(detailed_success)
        assert res is not None
        assert "resolution" in res["tags"]

    def test_knowledge_promotion_lifecycle(self, tmp_path: Path) -> None:
        from agent_runtime.knowledge import KnowledgeBase
        from agent_runtime.memory import create_memory_backend

        kb_dir = tmp_path / ".agent" / "knowledge_base"
        kb_dir.mkdir(parents=True, exist_ok=True)
        (kb_dir / "index.json").write_text("[]", encoding="utf-8")

        # Mock engine with a local memory backend
        engine = MagicMock()
        engine.config_path = tmp_path / ".agent" / "agent.md"
        engine.layout = {"directories": {"knowledge_base": kb_dir}}
        engine.memory = create_memory_backend("in_memory")

        # Write high-value episodic entry to memory backend
        episodic_id = "test_episodic_123"
        detailed_bug_entry = {
            "id": episodic_id,
            "timestamp": "2026-06-04T12:00:00Z",
            "role": "agent",
            "content": (
                "An issue with the document parser was resolved. The parser encountered a "
                "FileNotFoundError because it looked in the relative instead of absolute path. "
                "We fixed this bug by wrapping the resolution path in an absolute path resolver, "
                "which guarantees cross-project routing safety and prevents path traversal."
            )
        }
        engine.memory.write(episodic_id, detailed_bug_entry)

        kb = KnowledgeBase(engine)

        # 1. Promote episodic entry
        entry_meta = kb.promote(episodic_id)
        assert entry_meta["id"] == "kb_test_episodic_123"
        assert entry_meta["status"] == "draft"
        assert "bug-fix" in entry_meta["tags"]

        # Verify markdown file exists and has status: draft
        md_file = kb_dir / "test_episodic_123.md"
        assert md_file.exists()
        text = md_file.read_text(encoding="utf-8")
        assert "status: draft" in text
        assert "fixed this bug by wrapping" in text.lower()

        # Verify schema compliance if jsonschema is available
        try:
            import jsonschema as jsonschema_lib
        except ImportError:
            jsonschema_lib = None

        if jsonschema_lib is not None:
            schema_path = Path("spec/knowledge.schema.json")
            if schema_path.exists():
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                from tests.test_schemas import _load_frontmatter
                frontmatter = _load_frontmatter(md_file)
                jsonschema_lib.validate(instance=frontmatter, schema=schema)

        # Verify index.json was updated
        index_data = json.loads((kb_dir / "index.json").read_text(encoding="utf-8"))
        assert len(index_data) == 1
        assert index_data[0]["status"] == "draft"

        # 2. Confirm the draft to stable
        kb.confirm("kb_test_episodic_123")

        # Verify status updated to stable in markdown and index.json
        text_after = md_file.read_text(encoding="utf-8")
        assert "status: stable" in text_after
        assert "status: draft" not in text_after

        index_data_after = json.loads((kb_dir / "index.json").read_text(encoding="utf-8"))
        assert index_data_after[0]["status"] == "stable"

    def test_promote_fails_for_low_value_unless_forced(self, tmp_path: Path) -> None:
        from agent_runtime.knowledge import KnowledgeBase
        from agent_runtime.memory import create_memory_backend

        kb_dir = tmp_path / ".agent" / "knowledge_base"
        kb_dir.mkdir(parents=True, exist_ok=True)
        (kb_dir / "index.json").write_text("[]", encoding="utf-8")

        engine = MagicMock()
        engine.config_path = tmp_path / ".agent" / "agent.md"
        engine.layout = {"directories": {"knowledge_base": kb_dir}}
        engine.memory = create_memory_backend("in_memory")

        episodic_id = "low_value_entry"
        engine.memory.write(episodic_id, {"content": "short simple turn"})

        kb = KnowledgeBase(engine)

        # Should raise ValueError because it doesn't match heuristics
        with pytest.raises(ValueError, match="does not qualify for promotion"):
            kb.promote(episodic_id)

        # With force=True, it should pass
        entry_meta = kb.promote(episodic_id, force=True)
        assert entry_meta["id"] == "kb_low_value_entry"
        assert entry_meta["status"] == "draft"

    def test_cli_promote_and_confirm_integration(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        # Create minimal mock workspace
        agent_dir = tmp_path / ".agent"
        skills_dir = agent_dir / "skills"
        memory_dir = agent_dir / "memory"
        kb_dir = agent_dir / "knowledge_base"
        workflows_dir = agent_dir / "workflows"
        
        for directory in (skills_dir, memory_dir, kb_dir, workflows_dir):
            directory.mkdir(parents=True, exist_ok=True)

        (agent_dir / "skills.md").write_text("", encoding="utf-8")
        (tmp_path / "agent_tasks.md").write_text("", encoding="utf-8")
        (agent_dir / "handoff_guide.md").write_text("", encoding="utf-8")
        (kb_dir / "index.json").write_text("[]", encoding="utf-8")

        # Write agent manifest config
        config_path = agent_dir / "agent.md"
        config_path.write_text(f"""---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: "cli-kb-test"
version: "0.1.0"
purpose: "Test CLI promotion"
language: "en-US"
authorization_level: "autonomous"
use_case_tags: ["test"]
tools: []
protocol:
  root: ".agent/"
  manifest: ".agent/agent.md"
  entrypoints:
    skills: ".agent/skills.md"
    tasks: agent_tasks.md
    handoff: ".agent/handoff_guide.md"
  directories:
    skills: ".agent/skills/"
    workflows: ".agent/workflows/"
    memory: ".agent/memory/"
    knowledge_base: ".agent/knowledge_base/"
memory:
  backend: "local"
  path: "{memory_dir.as_posix()}/"
---
# Test Onboarding
""", encoding="utf-8")

        # Populate a high-value episodic entry in memory
        from agent_runtime.memory import JSONFileBackend
        mem = JSONFileBackend(path=memory_dir)
        episodic_id = "test_turn_99"
        mem.write(episodic_id, {
            "content": (
                "Solved a path resolution bug in the compiler tool. The tool failed to find "
                "the project root. We resolved the bug by using standard absolute path resolution "
                "and verifying the configuration existence dynamically in the local runtime sandbox."
            )
        })

        import sys
        from cli import main

        # 1. Run CLI promote
        orig_argv = sys.argv
        sys.argv = ["cli.py", "--config", str(config_path), "promote-knowledge", episodic_id, "--bypass-onboarding"]
        try:
            ret = main()
            assert ret == 0
        finally:
            sys.argv = orig_argv

        captured = capsys.readouterr()
        assert "Promoting episodic entry" in captured.out
        assert "Success: Promoted as draft semantic entry: kb_test_turn_99" in captured.out

        # 2. Run CLI confirm
        sys.argv = ["cli.py", "--config", str(config_path), "confirm-knowledge", "kb_test_turn_99", "--bypass-onboarding"]
        try:
            ret = main()
            assert ret == 0
        finally:
            sys.argv = orig_argv

        captured2 = capsys.readouterr()
        assert "Confirming knowledge entry 'kb_test_turn_99'" in captured2.out
        assert "Success: Knowledge entry 'kb_test_turn_99' confirmed and updated to stable" in captured2.out

