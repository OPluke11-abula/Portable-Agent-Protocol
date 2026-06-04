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

    def promote(self, episodic_entry_id: str, force: bool = False) -> dict[str, Any]:
        """Promote an episodic memory record to a semantic knowledge draft document.

        Parameters
        ----------
        episodic_entry_id : str
            The identifier of the episodic memory record to promote.
        force : bool, default False
            If True, bypasses the high-value heuristic check and forces promotion.

        Returns
        -------
        dict[str, Any]
            The metadata of the newly created semantic knowledge document.
        """
        # 1. Retrieve episodic entry from the engine's memory backend
        entry = self._engine.memory.read(episodic_entry_id)
        if entry is None:
            entry = self._engine.memory.read(f"episodic:{episodic_entry_id}")
        if entry is None:
            raise KeyError(f"Episodic memory entry '{episodic_entry_id}' not found in backend.")

        # Ensure the entry is a dict
        if isinstance(entry, str):
            try:
                entry = json.loads(entry)
            except json.JSONDecodeError:
                entry = {"content": entry, "id": episodic_entry_id}

        if not isinstance(entry, dict):
            raise TypeError("Episodic entry must be a dictionary or JSON-serializable structure")

        content = entry.get("content", "")
        if not content:
            raise ValueError(f"Episodic entry '{episodic_entry_id}' has no content to extract knowledge from.")

        # 2. Run heuristics unless force=True
        heuristics = extract_knowledge_heuristics(content)
        if not heuristics and not force:
            raise ValueError(
                f"Episodic entry '{episodic_entry_id}' does not qualify for promotion (does not match high-value heuristics)."
            )

        title = heuristics["title"] if heuristics else "Promoted Knowledge Entry"
        tags = heuristics["tags"] if heuristics else ["promoted"]

        # Ensure there is at least one tag to conform to the schema
        if not tags:
            tags = ["promoted"]

        # 3. Format valid safe ID: match ^[a-zA-Z0-9_-]+$
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", episodic_entry_id).strip("_")
        if not safe_id:
            import uuid
            safe_id = f"kb_{uuid.uuid4().hex}"
        elif not safe_id.startswith("kb_"):
            safe_id = f"kb_{safe_id}"

        # Check if already exists in index to prevent duplicate promotions
        if self._find_index_entry(safe_id) is not None:
            raise ValueError(f"Knowledge entry with ID '{safe_id}' already exists.")

        # 4. Write markdown file under .agent/knowledge_base/
        import datetime
        current_date = datetime.date.today().isoformat()
        md_filename = f"{safe_id.replace('kb_', '')}.md"
        md_file_path = self._kb_dir / md_filename

        # Construct YAML front-matter and content conforming to schema
        front_matter = {
            "id": safe_id,
            "title": title,
            "tags": tags,
            "created": current_date,
            "updated": current_date,
            "status": "draft"
        }

        # Write file with YAML frontmatter + content body
        yaml_text = yaml.safe_dump(front_matter, allow_unicode=True, default_flow_style=False)
        markdown_body = f"---\n{yaml_text}---\n\n# {title}\n\n{content}\n"
        
        self._kb_dir.mkdir(parents=True, exist_ok=True)
        md_file_path.write_text(markdown_body, encoding="utf-8")

        # 5. Append metadata entry to .agent/knowledge_base/index.json
        index_entry = {
            "id": safe_id,
            "title": title,
            "path": f".agent/knowledge_base/{md_filename}",
            "tags": tags,
            "created": current_date,
            "updated": current_date,
            "status": "draft"
        }

        # Update process-internal index
        self._index.append(index_entry)

        # Persist index.json
        index_json_path = self._kb_dir / "index.json"
        index_json_path.write_text(json.dumps(self._index, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info("Successfully promoted episodic entry '%s' to knowledge base as '%s'", episodic_entry_id, safe_id)
        return index_entry

    def confirm(self, entry_id: str) -> None:
        """Confirm a draft knowledge entry, setting its status to stable.

        Parameters
        ----------
        entry_id : str
            The identifier of the knowledge entry to confirm.
        """
        # Find entry in index
        entry_meta = self._find_index_entry(entry_id)
        if entry_meta is None:
            raise KeyError(f"Knowledge entry '{entry_id}' not found in index.")

        if entry_meta.get("status") != "draft":
            logger.info("Knowledge entry '%s' is already stable.", entry_id)
            return

        # 1. Update status in self._index
        entry_meta["status"] = "stable"
        import datetime
        current_date = datetime.date.today().isoformat()
        entry_meta["updated"] = current_date

        # Persist updated index.json
        index_json_path = self._kb_dir / "index.json"
        index_json_path.write_text(json.dumps(self._index, indent=2, ensure_ascii=False), encoding="utf-8")

        # 2. Update status in the corresponding .md file
        md_path = self._resolve_entry_path(entry_meta)
        if md_path is None or not md_path.exists():
            raise FileNotFoundError(f"Markdown file for entry '{entry_id}' not found on disk.")

        text = md_path.read_text(encoding="utf-8")
        match = _FRONTMATTER_RE.match(text)
        if not match:
            raise ValueError(f"Malformed markdown file for entry '{entry_id}' (missing frontmatter).")

        # Load and update frontmatter
        try:
            front_matter = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML frontmatter in '{entry_id}': {e}") from e

        front_matter["status"] = "stable"
        front_matter["updated"] = current_date

        # Re-write the markdown file
        yaml_text = yaml.safe_dump(front_matter, allow_unicode=True, default_flow_style=False)
        content = text[match.end():]
        new_markdown = f"---\n{yaml_text}---\n{content}"
        
        md_path.write_text(new_markdown, encoding="utf-8")
        logger.info("Successfully confirmed knowledge entry '%s' and updated status to stable", entry_id)


def extract_knowledge_heuristics(content: str) -> dict[str, Any] | None:
    """Analyze the content of an episodic memory entry to check if it qualifies as high-value.

    Parameters
    ----------
    content : str
        The textual content of the episodic entry.

    Returns
    -------
    dict[str, Any] | None
        Heuristic evaluation metadata (title, tags, reasons, confidence) if high-value, else None.
    """
    if not content:
        return None

    content_lower = content.lower()

    # 1. Solved environment/tool bugs
    bug_keywords = ["bug", "fixed", "workaround", "patch", "resolved", "error", "exception", "failed to", "solved", "work around", "fix"]
    has_bug = any(kw in content_lower for kw in bug_keywords)

    # 2. Repeated successful patterns / complex workflow resolutions
    pattern_keywords = ["successful pattern", "workflow resolution", "best practice", "optimized", "conformance", "conformance check", "pipeline", "reproducible", "pattern", "resolution"]
    has_pattern = any(kw in content_lower for kw in pattern_keywords)

    # 3. High quality length/structure criteria
    has_min_info = len(content) > 150

    tags = []
    reasons = []

    if has_bug and has_min_info:
        tags.append("bug-fix")
        reasons.append("Solved environment or tool bug with detailed description")
    if has_pattern and has_min_info:
        tags.append("best-practice")
        reasons.append("Workflow resolution pattern or optimization identified")

    # If it is detailed and successful but doesn't hit specific keywords
    if has_min_info and not tags and ("success" in content_lower or "resolved" in content_lower or "completed" in content_lower):
        tags.append("resolution")
        reasons.append("Detailed successful resolution logs")

    if tags:
        # Generate title from first line or sentence (max 100 chars)
        first_line = content.strip().split("\n")[0]
        title_match = re.match(r"^([^.]+)", first_line)
        title = title_match.group(1)[:100].strip() if title_match else first_line[:100].strip()
        if not title or len(title) < 5:
            title = "Extracted Knowledge Resolution"
        
        return {
            "title": title,
            "tags": tags,
            "reasons": reasons,
            "confidence": "high" if len(reasons) > 1 else "medium"
        }

    return None

