# Memory Entry Point

This file defines the runtime-facing memory schema used by the Portable Agent.
Strategy notes for short-term and long-term memory live under `.agent/memory/`.

---

## Overview

The agent persists context between invocations using a pluggable **Memory
Backend** system.  The `backend` field in `agent.md` selects which
implementation to use at runtime.

```yaml
# in agent.md front matter
memory:
  backend: local        # or: in_memory, sqlite, vector
  path: .agent/memory/
```

---

## Backends

| Backend     | Class              | Description                                      |
| ----------- | ------------------ | ------------------------------------------------ |
| `in_memory` | `InMemoryBackend`  | Ephemeral dict store, zero dependencies.  Data lost on exit. |
| `local`     | `JSONFileBackend`  | JSON file persistence at `memory.json` (default). |
| `json`      | `JSONFileBackend`  | Alias for `local`.                               |
| `sqlite`    | `SQLiteBackend`    | SQLite database for durable local persistence.   |
| `vector`    | `VectorDBBackend`  | Placeholder for semantic search (Qdrant / Chroma). |

### API Contract

Every backend implements the `MemoryBackend` abstract class:

```python
class MemoryBackend(ABC):
    def read(self, key: str) -> Any: ...
    def write(self, key: str, value: Any) -> None: ...
    def delete(self, key: str) -> bool: ...
    def list_keys(self) -> list[str]: ...
    def search(self, query: str, top_k: int = 5) -> list[dict]: ...
    def clear(self) -> None: ...
```

### Usage Example

```python
from agent_runtime.memory import create_memory_backend

# Factory-based creation
backend = create_memory_backend("sqlite", path=".agent/memory/memory.db")
backend.write("user_name", "Alice")
print(backend.read("user_name"))   # "Alice"
print(backend.search("ali"))       # [{"key": "user_name", "value": "Alice"}]
```

Or via the `AgentEngine`:

```python
from agent_runtime import AgentEngine

engine = AgentEngine(".agent/agent.md")
engine.memory.write("session_id", "abc-123")
print(engine.memory.read("session_id"))
```

---

## Schema

### context.json

```json
{
  "session_id": "<uuid>",
  "started_at": "<ISO-8601 timestamp>",
  "variables": {
    "<key>": "<value>"
  }
}
```

### history.json

```json
[
  {
    "id": "<uuid>",
    "timestamp": "<ISO-8601>",
    "role": "user | agent",
    "content": "<message or tool result>",
    "tool": "<tool name or null>"
  }
]
```

### Skill writeback records

Anthropic-aware skill execution writes one markdown record per invocation:

```text
.agent/memory/<skill_name>/<session_id>.md
```

Each record contains the timestamp, session id, JSON-encoded params, and
JSON-encoded result. Routers that dispatch through external skill runtimes must
load recent records before execution and append a new record after a successful
result.

---

## Supporting memory guidance

See:

- `.agent/memory/__init__.md`
- `.agent/memory/short_term_cache.md`
- `.agent/memory/vector_db.md`
