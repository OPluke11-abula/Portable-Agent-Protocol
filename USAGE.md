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

## 6. Reference CLI Tool

The Portable Agent Protocol includes a reference command-line interface (`cli.py`) that implements core runtime behaviors such as validation, skill discovery, persistent memory read/write, workflow execution, and registry/hub sync.

### Initialization & Validation

*   **Initialize a new workspace**: Creates the required `.agent/` folder structure, manifest, templates, and directories.
    ```bash
    python cli.py init
    ```
*   **Validate the workspace**: Verifies that the `.agent/` folder layout and manifest file strictly conform to the official protocol schemas.
    ```bash
    python cli.py validate
    # OR using the --validate flag:
    python cli.py --validate
    ```

### Skill Contract Discovery

*   **List all active skill contracts**: Scans `.agent/skills/` and lists the ID, version, and description of all declared capability contracts.
    ```bash
    python cli.py --list-skills
    ```
*   **Describe a single skill contract**: Prints the complete YAML/JSON front-matter contract (inputs, outputs, safety boundaries) for a specific skill.
    ```bash
    python cli.py --describe-skill search_web
    ```

### Persistent Memory Operations

*   **Write to memory**: Persists a key-value pair to the persistent SQLite/JSON memory backend.
    ```bash
    python cli.py --memory-write "key_name" "value_or_json"
    ```
*   **Read from memory**: Reads a stored key value from the persistent memory backend.
    ```bash
    python cli.py --memory-read "key_name"
    ```

### Workflow Execution

*   **Run a workflow**: Executes a multi-step execution graph defined under `.agent/workflows/`.
    ```bash
    python cli.py --run-workflow "workflow_id" --params '{"input_arg": "value"}'
    ```

### MCP & Hub Synchronization

*   **Sync Model Context Protocol (MCP) servers**: Dynamically pulls active MCP tools and registers/scaffolds their matching capability contracts.
    ```bash
    python cli.py mcp sync
    ```
*   **Pack workspace for sharing**: Packages the local `.agent/` configuration into a portable tarball, automatically excluding memory and credentials.
    ```bash
    python cli.py hub pack
    ```
*   **Clone workspace from Hub**: Clones a remote agent's `.agent/` configuration profile from the Hub.
    ```bash
    python cli.py hub clone "username/repo"
    ```



