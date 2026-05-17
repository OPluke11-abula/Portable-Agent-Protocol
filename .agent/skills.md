# Skills

This document is the high-level skill catalogue for the Portable Agent.

The detailed skill contracts now live in `.agent/skills/*.md`, while this file stays as the runtime-facing index.

## Runtime skill modules

- `search_web` -> `agent_runtime/tools/search_web.py`
- `query_db` -> `agent_runtime/tools/query_db.py`
- `code_executor` -> `agent_runtime/tools/code_executor.py`

## Detailed protocol specs

See:

- `.agent/skills/search_web.md`
- `.agent/skills/query_db.md`
- `.agent/skills/code_executor.md`

## Adding new skills

1. Create `agent_runtime/tools/<skill_name>.py`
2. Implement a `run(params: dict) -> dict` function
3. Add the skill name to `tools:` in `.agent/agent.md`
4. Add a matching protocol document under `.agent/skills/`
