# Portable-Agent-Protocol

Portable `.agent` protocol and Python reference runtime for AI collaboration, skills, memory, prompts, and self-evolving workflows.

## What this repository contains

- `.agent/`: the protocol source of truth, including manifest, core specs, skills, prompts, memory, and knowledge base templates
- `agent_runtime/`: a Python reference implementation that can load and execute the protocol
- `tests/`: basic tests for the runtime
- `examples/`: protocol writeback and runtime simulation examples
- `USAGE.md`: instructions for copying the `.agent/` workspace into another repository

## Structure

```text
.
├─ .agent/
│  ├─ agent.md
│  ├─ core/
│  ├─ skills/
│  ├─ prompts/
│  ├─ memory/
│  ├─ knowledge_base/
│  ├─ skills.md
│  ├─ prompts.md
│  ├─ memory.md
│  └─ workflows.md
├─ agent_runtime/
├─ tests/
├─ examples/
├─ cli.py
├─ pyproject.toml
└─ USAGE.md
```

## Notes

- The YAML front matter in `.agent/agent.md` is used by the Python runtime.
- The subdirectories under `.agent/` provide richer protocol documentation and reusable templates.
- The flat `.agent/*.md` files remain valid entrypoints for the runtime.
