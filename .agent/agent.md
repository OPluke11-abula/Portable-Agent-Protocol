---
name: portable-agent
version: "0.1.0"
description: >
  Reference implementation of the Portable Agent Protocol —
  a minimal, portable runtime for AI collaboration, skills, memory,
  prompts, and self-evolving project workflows.
tools:
  - search_web
  - query_db
  - code_executor
memory:
  backend: local
  path: .agent/memory/
prompts:
  path: .agent/prompts.md
workflows:
  path: .agent/workflows.md
---

# Agent Protocol — agent.md

This file is the **source-of-truth configuration** for the Portable Agent.
The Python runtime reads the YAML front-matter above to bootstrap itself.

## What this agent does

- Routes natural-language or structured requests to the right tool.
- Maintains a local memory store for context persistence.
- Loads prompt templates from `prompts.md`.
- Executes workflows defined in `workflows.md`.

## Extending the agent

1. Add a new tool module under `agent_runtime/tools/`.
2. Register its name in the `tools:` list above.
3. The router will automatically discover and dispatch to it.

See `skills.md` for the full capability catalogue.
