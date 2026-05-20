"""Knowledge Base module for the Portable Agent Protocol.

Provides read-only access to durable project knowledge stored in
``.agent/knowledge_base/``.  Each knowledge entry is a Markdown file
with YAML front-matter conforming to ``spec/knowledge.schema.json``.

Write operations are intentionally forbidden at runtime — any mutation
must go through the T-04 Protocol Evolution process.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from .logger import get_logger

if TYPE_CHECKING:
    from .engine import AgentEngine

logger = get_logger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class KnowledgeBase:
    """Read-only interface over ``.agent/knowledge_base/`` entries.

    Parameters
    ----------
    engine : AgentEngine
        The parent engine, used to resolve the knowledge-base directory
        from the agent manifest layout.
    """

    def __init__(self, engine: AgentEngine) -> None:
        self._engine = engine

        # Resolve the knowledge_base directory from the layout or fallback
        kb_dir: Path | None = None
        layout = getattr(engine, "layout", None)
        if isinstance(layout, dict):
            kb_dir = layout.get("directories", {}).get("knowledge_base")
        if kb_dir is None:
            kb_dir = engine.config_path.parent / "knowledge_base"
        self._kb_dir = Path(kb_dir)

        # Load the index registry (if present)
        self._index: list[dict[str, Any]] = []
        index_path = self._kb_dir / "index.json"
        if index_path.exists():
            try:
                self._index = json.loads(index_path.read_text(encoding="utf-8"))
                logger.debug("Loaded knowledge index with %d entries", len(self._index))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load knowledge index: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, entry_id: str) -> dict[str, Any] | None:
        """Return a single knowledge entry by *entry_id*.

        The returned dict contains the front-matter metadata **plus** a
        ``"content"`` key holding the Markdown body (everything after the
        closing ``---``).

        Returns ``None`` if no entry with *entry_id* exists.
        """
        entry_meta = self._find_index_entry(entry_id)
        if entry_meta is None:
            return None

        md_path = self._resolve_entry_path(entry_meta)
        if md_path is None or not md_path.exists():
            logger.warning("Knowledge entry file missing for id=%s", entry_id)
            return None

        return self._parse_entry(md_path)

    def query(self, keyword: str) -> list[dict[str, Any]]:
        """Search knowledge entries by *keyword*.

        Performs a **case-insensitive** substring match across:
        - ``title``
        - ``tags``
        - full Markdown body content

        Returns a list of matching entries (metadata + content).
        """
        keyword_lower = keyword.lower()
        results: list[dict[str, Any]] = []

        for meta in self._index:
            md_path = self._resolve_entry_path(meta)
            if md_path is None or not md_path.exists():
                continue

            parsed = self._parse_entry(md_path)
            if parsed is None:
                continue

            # Match against title
            if keyword_lower in parsed.get("title", "").lower():
                results.append(parsed)
                continue

            # Match against tags
            tags = parsed.get("tags", [])
            if any(keyword_lower in t.lower() for t in tags):
                results.append(parsed)
                continue

            # Match against full body content
            if keyword_lower in parsed.get("content", "").lower():
                results.append(parsed)

        return results

    def list_entries(self) -> list[dict[str, Any]]:
        """Return the full index metadata (without content bodies)."""
        return list(self._index)

    # ------------------------------------------------------------------
    # Write Protection
    # ------------------------------------------------------------------

    def write(self, entry_id: str, data: Any) -> None:
        """Raise — knowledge base is read-only at runtime."""
        raise PermissionError(
            f"Cannot write to knowledge base entry '{entry_id}'. "
            "The knowledge base is read-only at runtime. "
            "Any mutation must go through the T-04 Protocol Evolution process."
        )

    def update(self, entry_id: str, data: Any) -> None:
        """Raise — knowledge base is read-only at runtime."""
        raise PermissionError(
            f"Cannot update knowledge base entry '{entry_id}'. "
            "The knowledge base is read-only at runtime. "
            "Any mutation must go through the T-04 Protocol Evolution process."
        )

    def delete(self, entry_id: str) -> None:
        """Raise — knowledge base is read-only at runtime."""
        raise PermissionError(
            f"Cannot delete knowledge base entry '{entry_id}'. "
            "The knowledge base is read-only at runtime. "
            "Any mutation must go through the T-04 Protocol Evolution process."
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_index_entry(self, entry_id: str) -> dict[str, Any] | None:
        """Locate an entry in the index by its ``id``."""
        for entry in self._index:
            if entry.get("id") == entry_id:
                return entry
        return None

    def _resolve_entry_path(self, meta: dict[str, Any]) -> Path | None:
        """Resolve the filesystem path for a knowledge entry."""
        raw_path = meta.get("path")
        if raw_path is None:
            return None

        candidate = Path(raw_path)
        if candidate.is_absolute() and candidate.exists():
            return candidate

        # Try relative to project root (parent of .agent/)
        project_root = self._engine.config_path.parent.parent
        resolved = project_root / candidate
        if resolved.exists():
            return resolved

        # Fall back to relative to knowledge_base dir
        resolved_kb = self._kb_dir / candidate.name
        if resolved_kb.exists():
            return resolved_kb

        return None

    @staticmethod
    def _parse_entry(path: Path) -> dict[str, Any] | None:
        """Parse a knowledge Markdown file into metadata + content."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None

        match = _FRONTMATTER_RE.match(text)
        if not match:
            return None

        try:
            metadata: dict[str, Any] = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return None

        # Content is everything after the closing front-matter fence
        content = text[match.end():]
        metadata["content"] = content.strip()
        return metadata
