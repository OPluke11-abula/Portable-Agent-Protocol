# .agent Architecture

This `.agent/` workspace is organized in three layers so the Python runtime and
the richer protocol templates can coexist without ambiguity.

## Layer 1: Executable manifest

- `.agent/agent.md` is the executable manifest.
- The current Python reference runtime parses the YAML front matter in this file
  and discovers the declared protocol layout.
- Runtime paths and top-level layout declarations must stay accurate here.

## Layer 2: Runtime entry documents

These top-level files are stable entrypoints for agents and future runtimes:

- `.agent/skills.md`: runtime skill registry and module map
- `.agent/prompts.md`: runtime prompt catalog and reusable prompt snippets
- `.agent/memory.md`: persistence schema and backend contract
- `.agent/workflows.md`: canonical workflow registry

## Layer 3: Detailed protocol directories

These directories hold deeper contracts, design notes, and reusable templates:

- `.agent/core/`: engine, router, and logger responsibilities
- `.agent/skills/`: per-skill contracts and safety notes
- `.agent/prompts/`: prompt-authoring and error-handling guidance
- `.agent/memory/`: short-term and long-term memory strategy notes
- `.agent/workflows/`: per-workflow notes and usage guidance
- `.agent/knowledge_base/`: durable project knowledge

## Source of Truth Rules

- Runtime configuration: `.agent/agent.md`
- Runtime registry data: the matching top-level entry document
- Detailed guidance and rationale: the matching subdirectory
- If a top-level entry document and a leaf document overlap, the top-level entry
  document defines the runtime-facing contract and the leaf document adds
  detail, examples, or policy guidance.

## Recommended Read Order

1. `.agent/agent.md`
2. `.agent/README.md`
3. The relevant top-level entry document
4. The relevant leaf documents in subdirectories

## Writeback Rules

- New runtime capability: update `.agent/agent.md`, `.agent/skills.md`, the
  Python runtime module, and the matching `.agent/skills/*.md`
- New prompt policy: update `.agent/prompts/`
- New workflow: update `.agent/workflows.md` and add a note under
  `.agent/workflows/`
- Stable cross-task knowledge: update `.agent/knowledge_base/`
- Session-local state conventions: update `.agent/memory/`
