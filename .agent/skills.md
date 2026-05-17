# Skills Entry Point

This file is the runtime-facing skill registry for the Portable Agent.

Use it to map tool names to Python modules. Detailed per-skill contracts live in
`.agent/skills/*.md`.

## Runtime skill modules

- `search_web` -> `agent_runtime/tools/search_web.py`
- `query_db` -> `agent_runtime/tools/query_db.py`
- `code_executor` -> `agent_runtime/tools/code_executor.py`

## Detailed protocol specs

See:

- `.agent/skills/__init__.md`
- `.agent/skills/search_web.md`
- `.agent/skills/query_db.md`
- `.agent/skills/code_executor.md`

## Adding new skills

1. Create `agent_runtime/tools/<skill_name>.py`
2. Implement a `run(params: dict) -> dict` function
3. Add the skill name to `tools:` in `.agent/agent.md`
4. Add a matching protocol document under `.agent/skills/`
5. Update this file if the runtime registry changes
