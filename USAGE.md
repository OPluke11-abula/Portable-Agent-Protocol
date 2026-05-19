# FPAP Usage Guide

Use this guide when copying the `.agent/` protocol workspace into another
repository.

## 1. Copy the protocol workspace

```text
cp -r .agent /your-project/.agent
```

On Windows, macOS, or Linux, the exact copy command can differ. Preserve the
directory structure under `.agent/`.

## 2. Tell the agent how to read it

Give the receiving AI agent this instruction:

```text
Read .agent/agent.md first, then .agent/README.md. Treat .agent/ as a
three-layer protocol workspace: manifest, runtime entry documents, and detailed
directories. Use .agent/skills.md, .agent/prompts.md, .agent/memory.md, and
.agent/workflows.md as runtime-facing entry documents. Use .agent/core/,
.agent/skills/, .agent/prompts/, .agent/memory/, .agent/workflows/, and
.agent/knowledge_base/ for deeper guidance and templates.
```

## 3. Recommended read order

1. `.agent/agent.md`
2. `.agent/README.md`
3. The relevant top-level entry document:
   `.agent/skills.md`, `.agent/prompts.md`, `.agent/memory.md`, or
   `.agent/workflows.md`
4. The relevant detailed documents:
   `.agent/core/*.md`, `.agent/skills/*.md`, `.agent/prompts/*.md`,
   `.agent/memory/*.md`, or `.agent/workflows/*.md`
5. `.agent/knowledge_base/*`

## 4. Writeback rules

- New runtime capability: update `.agent/agent.md`, `.agent/skills.md`, the
  runtime implementation, and the matching `.agent/skills/*.md` file.
- New prompt policy: update `.agent/prompts/`.
- New workflow: update `.agent/workflows.md` and add a note under
  `.agent/workflows/`.
- Session-local memory convention: update `.agent/memory/`.
- Durable cross-task knowledge: update `.agent/knowledge_base/`.
- Runtime path changes must be reflected in `.agent/agent.md`.

## 5. Runtime-generated files

If a downstream project adds runtime state, logs, generated skill code, or
temporary artifacts, keep those files separate from the stable protocol
documents. Recommended generated paths include:

- `.agent/runtime/`
- `.agent/logs/`
- `.agent/memory/vector_store/`
- `.agent/memory/chroma/`

These paths are ignored in this repository so generated runtime data does not
drift into the protocol template by accident.

## 6. Anthropic skills interoperability

Export local PAP skill contracts as Anthropic-style skill folders:

```text
python cli.py --export-skills --output ./anthropic_skills/
```

Sync a local Anthropic skills checkout into the PAP registry:

```text
python cli.py --sync-anthropic-skills --source ./path/to/anthropics/skills/
```

Sync directly from GitHub without cloning:

```text
python cli.py --sync-anthropic-skills --source github:anthropics/skills
```

Validate that local PAP skills can be exported:

```text
python cli.py --validate-compatibility
```

Dispatching through Claude API is optional and requires `ANTHROPIC_API_KEY`:

```text
python cli.py --tool search_web --params '{"query":"test"}' --via-claude-api --anthropic-skill-id skill_01Example --anthropic-skill-type custom
```

For Claude API Skills, exported local folders must be uploaded to Anthropic
first, or the command must reference an existing Anthropic built-in skill id.
PAP uses that id in the Messages API `container.skills` field and writes the
execution result back to `.agent/memory/<skill>/<session>.md`.
