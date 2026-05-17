# Portable-Agent-Protocol

Portable `.agent` protocol and Python reference runtime for AI collaboration,
skills, memory, prompts, and self-evolving workflows.

## What this repository contains

- `.agent/`: the protocol source of truth, including the manifest, runtime
  entry documents, core specs, skill contracts, prompts, memory guidance,
  workflow notes, and knowledge base templates
- `agent_runtime/`: a Python reference implementation that can load and execute
  the protocol
- `tests/`: basic tests for the runtime
- `examples/`: protocol writeback and runtime simulation examples
- `USAGE.md`: instructions for copying the `.agent/` workspace into another
  repository

## Structure

```text
.
├─ .agent/
│  ├─ agent.md
│  ├─ README.md
│  ├─ core/
│  ├─ skills/
│  ├─ prompts/
│  ├─ memory/
│  ├─ workflows/
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

- The YAML front matter in `.agent/agent.md` is the executable manifest used by
  the Python runtime.
- `.agent/README.md` explains the three-layer layout: manifest, runtime entry
  documents, and detailed protocol directories.
- The top-level `.agent/*.md` files are runtime-facing entry documents.
- The subdirectories under `.agent/` provide richer protocol documentation,
  templates, and workflow notes.
