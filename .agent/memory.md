# Memory

This document describes the memory schema used by the Portable Agent.

---

## Overview

The agent persists context between invocations using a **local JSON store**
located at `.agent/memory/`.  Each key maps to a JSON file:

```
.agent/memory/
  context.json      — current session context
  history.json      — ordered list of past interactions
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

| Backend  | Description                         |
|----------|-------------------------------------|
| `local`  | Plain JSON files (default)          |
| `sqlite` | SQLite database (planned)           |
| `redis`  | Redis key-value store (planned)     |
