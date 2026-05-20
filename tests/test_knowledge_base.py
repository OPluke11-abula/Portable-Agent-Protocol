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
