"""Pluggable memory backend abstraction for the Portable Agent Protocol.

This module defines the ``MemoryBackend`` abstract base class and ships three
reference implementations:

* **InMemoryBackend** – zero-dependency, ephemeral store for development and
  testing.
* **JSONFileBackend** – lightweight local persistence using plain JSON files
  (the original PAP default).
* **SQLiteBackend** – durable local persistence via a single SQLite database.

A fourth placeholder, **VectorDBBackend**, is provided for future semantic
search integration (e.g. Qdrant, Chroma).

Usage
-----
>>> from agent_runtime.memory import create_memory_backend
>>> backend = create_memory_backend("in_memory")
>>> backend.write("greeting", "hello")
>>> backend.read("greeting")
'hello'
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Abstract Base Class
# ---------------------------------------------------------------------------

class MemoryBackend(ABC):
    """Abstract interface that every PAP memory backend must implement."""

    @abstractmethod
    def read(self, key: str) -> Any:
        """Return the value stored under *key*, or ``None`` if absent."""

    @abstractmethod
    def write(self, key: str, value: Any) -> None:
        """Persist *value* under *key*."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove *key* from the store.  Return ``True`` if it existed."""

    @abstractmethod
    def list_keys(self) -> list[str]:
        """Return all keys currently stored."""

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Return up to *top_k* entries whose key or value match *query*.

        This is a simple substring search for basic backends.  Semantic
        backends (e.g. VectorDB) should override with embedding-based
        retrieval.
        """

    @abstractmethod
    def clear(self) -> None:
        """Remove **all** entries from the store."""


# ---------------------------------------------------------------------------
# InMemoryBackend – ephemeral, zero-dependency
# ---------------------------------------------------------------------------

class InMemoryBackend(MemoryBackend):
    """Dictionary-backed in-memory store.  Data is lost on process exit."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._timestamps: dict[str, float] = {}
        logger.info("InMemoryBackend initialised (ephemeral)")

    def read(self, key: str) -> Any:
        return self._store.get(key)

    def write(self, key: str, value: Any) -> None:
        self._store[key] = value
        self._timestamps[key] = time.time()

    def delete(self, key: str) -> bool:
        existed = key in self._store
        self._store.pop(key, None)
        self._timestamps.pop(key, None)
        return existed

    def list_keys(self) -> list[str]:
        return list(self._store.keys())

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        q = query.lower()
        for key, value in self._store.items():
            if q in key.lower() or q in str(value).lower():
                results.append({"key": key, "value": value})
                if len(results) >= top_k:
                    break
        return results

    def clear(self) -> None:
        self._store.clear()
        self._timestamps.clear()


# ---------------------------------------------------------------------------
# JSONFileBackend – plain JSON file persistence (original PAP default)
# ---------------------------------------------------------------------------

class JSONFileBackend(MemoryBackend):
    """Persists each key as a field in a single JSON file.

    Parameters
    ----------
    path : str | Path
        Directory where ``memory.json`` will be stored.
    """

    def __init__(self, path: str | Path = ".agent/memory/") -> None:
        self._dir = Path(path)
        self._file = self._dir / "memory.json"
        self._lock = threading.Lock()
        logger.info("JSONFileBackend initialised at %s", self._file)

    # -- internal helpers ---------------------------------------------------

    def _load(self) -> dict[str, Any]:
        try:
            return json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save(self, data: dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # -- public API ---------------------------------------------------------

    def read(self, key: str) -> Any:
        with self._lock:
            return self._load().get(key)

    def write(self, key: str, value: Any) -> None:
        with self._lock:
            data = self._load()
            data[key] = value
            self._save(data)

    def delete(self, key: str) -> bool:
        if not self._file.exists():
            return False
        with self._lock:
            data = self._load()
            existed = key in data
            data.pop(key, None)
            self._save(data)
            return existed

    def list_keys(self) -> list[str]:
        with self._lock:
            return list(self._load().keys())

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        q = query.lower()
        with self._lock:
            for key, value in self._load().items():
                if q in key.lower() or q in str(value).lower():
                    results.append({"key": key, "value": value})
                    if len(results) >= top_k:
                        break
        return results

    def clear(self) -> None:
        if not self._file.exists():
            return
        with self._lock:
            self._save({})


# ---------------------------------------------------------------------------
# SQLiteBackend – durable local persistence
# ---------------------------------------------------------------------------

class SQLiteBackend(MemoryBackend):
    """SQLite-backed memory store for durable local persistence.

    Parameters
    ----------
    db_path : str | Path
        Path to the SQLite database file.  Created automatically if absent.
    """

    _DDL = """
    CREATE TABLE IF NOT EXISTS memory (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at REAL NOT NULL
    );
    """

    def __init__(self, db_path: str | Path = ".agent/memory/memory.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._lock = threading.Lock()
        with self._conn:
            self._conn.execute(self._DDL)
        logger.info("SQLiteBackend initialised at %s", self._db_path)

    # -- public API ---------------------------------------------------------

    def read(self, key: str) -> Any:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM memory WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def write(self, key: str, value: Any) -> None:
        serialised = json.dumps(value, ensure_ascii=False)
        with self._lock:
            with self._conn:
                self._conn.execute(
                    "INSERT OR REPLACE INTO memory (key, value, updated_at) "
                    "VALUES (?, ?, ?)",
                    (key, serialised, time.time()),
                )

    def delete(self, key: str) -> bool:
        with self._lock:
            with self._conn:
                cursor = self._conn.execute(
                    "DELETE FROM memory WHERE key = ?", (key,)
                )
        return cursor.rowcount > 0

    def list_keys(self) -> list[str]:
        with self._lock:
            rows = self._conn.execute("SELECT key FROM memory").fetchall()
        return [r[0] for r in rows]

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        pattern = f"%{query}%"
        with self._lock:
            rows = self._conn.execute(
                "SELECT key, value FROM memory "
                "WHERE key LIKE ? OR value LIKE ? LIMIT ?",
                (pattern, pattern, top_k),
            ).fetchall()
        return [{"key": r[0], "value": json.loads(r[1])} for r in rows]

    def clear(self) -> None:
        with self._lock:
            with self._conn:
                self._conn.execute("DELETE FROM memory")


# ---------------------------------------------------------------------------
# VectorDBBackend – placeholder for semantic search (future)
# ---------------------------------------------------------------------------

class VectorDBBackend(MemoryBackend):
    """Placeholder for embedding-based semantic search backends.

    To use a real VectorDB (Qdrant, Chroma, etc.), subclass this and
    override all methods with your embedding + retrieval logic.
    """

    def __init__(self, **kwargs: Any) -> None:  # noqa: ARG002
        logger.warning(
            "VectorDBBackend is a placeholder. "
            "Override with a real implementation for production use."
        )
        self._fallback = InMemoryBackend()

    def read(self, key: str) -> Any:
        return self._fallback.read(key)

    def write(self, key: str, value: Any) -> None:
        self._fallback.write(key, value)

    def delete(self, key: str) -> bool:
        return self._fallback.delete(key)

    def list_keys(self) -> list[str]:
        return self._fallback.list_keys()

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self._fallback.search(query, top_k)

    def clear(self) -> None:
        self._fallback.clear()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_BACKENDS: dict[str, type[MemoryBackend]] = {
    "in_memory": InMemoryBackend,
    "local": JSONFileBackend,
    "json": JSONFileBackend,
    "sqlite": SQLiteBackend,
    "vector": VectorDBBackend,
}


def create_memory_backend(
    backend_name: str = "local",
    *,
    path: str | Path | None = None,
    **kwargs: Any,
) -> MemoryBackend:
    """Instantiate a memory backend by name.

    Parameters
    ----------
    backend_name : str
        One of ``"in_memory"``, ``"local"`` / ``"json"``, ``"sqlite"``,
        or ``"vector"``.
    path : str | Path | None
        Override the default storage path for file-backed backends.
    **kwargs
        Extra keyword arguments forwarded to the backend constructor.
    """
    cls = _BACKENDS.get(backend_name.lower())
    if cls is None:
        raise ValueError(
            f"Unknown memory backend '{backend_name}'. "
            f"Available: {', '.join(sorted(_BACKENDS))}"
        )

    # Inject path when the backend accepts it
    if path is not None and cls in (JSONFileBackend, SQLiteBackend):
        if cls is JSONFileBackend:
            return cls(path=path, **kwargs)
        return cls(db_path=path, **kwargs)

    return cls(**kwargs)
