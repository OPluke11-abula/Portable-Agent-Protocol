# Memory Entry Point

This file defines the runtime-facing memory schema used by the Portable Agent.
Strategy notes for short-term and long-term memory live under `.agent/memory/`.

---

## Overview

The agent persists context between invocations using a local JSON store located
at `.agent/memory/`. Each key maps to a JSON file:

```text
.agent/memory/
  context.json      current session context
  history.json      ordered list of past interactions
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

---

## Backends

The `backend` field in `agent.md` controls the persistence layer.

| Backend | Description |
| --- | --- |
| `local` | Plain JSON files (default) |
| `sqlite` | SQLite database (planned) |
| `redis` | Redis key-value store (planned) |

---

## Supporting memory guidance

See:

- `.agent/memory/__init__.md`
- `.agent/memory/short_term_cache.md`
- `.agent/memory/vector_db.md`
