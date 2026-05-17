# Skills

This document catalogues all skills (tools) available to the Portable Agent.

---

## search_web

**Module:** `agent_runtime/tools/search_web.py`

Performs a web search and returns a ranked list of results.

### Input

| Field   | Type   | Required | Description          |
|---------|--------|----------|----------------------|
| `query` | string | yes      | Search query string  |
| `limit` | int    | no       | Max results (default 5) |

### Output

List of `{"title": str, "url": str, "snippet": str}` objects.

---

## query_db

**Module:** `agent_runtime/tools/query_db.py`

Executes a read-only SQL query against a configured database.

### Input

| Field   | Type   | Required | Description        |
|---------|--------|----------|--------------------|
| `sql`   | string | yes      | SQL SELECT statement |
| `db`    | string | no       | Named connection (default `"default"`) |

### Output

List of row dictionaries.

---

## code_executor

**Module:** `agent_runtime/tools/code_executor.py`

Runs a snippet of Python code in a sandboxed environment and returns stdout/stderr.

### Input

| Field    | Type   | Required | Description                  |
|----------|--------|----------|------------------------------|
| `code`   | string | yes      | Python source to execute     |
| `timeout`| int    | no       | Seconds before timeout (default 10) |

### Output

```json
{"stdout": "...", "stderr": "...", "exit_code": 0}
```

---

## Adding new skills

1. Create `agent_runtime/tools/<skill_name>.py`.
2. Implement a `run(params: dict) -> dict` function.
3. Add the skill name to `tools:` in `.agent/agent.md`.
