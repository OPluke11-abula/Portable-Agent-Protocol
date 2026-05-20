# Portable Agent Protocol (PAP)

[![PAP Compatible](https://img.shields.io/badge/PAP--Compatible-blue.svg)](https://github.com/OPluke11-abula/Portable-Agent-Protocol)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)]()

Portable Agent Protocol is a portable `.agent/` workspace specification plus a
Python reference runtime. It separates an agent's durable collaboration state
from the runtime that executes tools, routes work, manages memory, and applies
workflow contracts.

The repository has two identities:

- A protocol workspace template under `.agent/`
- A Python reference runtime under `agent_runtime/`

That split is intentional. The `.agent/` files describe the portable contract;
the runtime proves that the contract can be loaded, validated, routed, and
executed.

## Why PAP Exists

Modern AI tooling is fragmented across IDE agents, chat products, local
runtimes, MCP tools, and vendor-specific skill formats. PAP gives projects a
stable workspace that can travel between those environments:

- `agent.md` declares the executable manifest and layout.
- `skills.md` registers local and external skills.
- `prompts.md` owns prompt policy and reusable prompt fragments.
- `memory.md` defines durable context conventions.
- `workflows.md` describes repeatable multi-step execution.

An agent can clone a project, read `.agent/agent.md`, and recover the project's
collaboration contract without relying on one vendor's runtime state.

## Agent Onboarding & Bootstrapping (.AGENT)

To enable incoming AI agents to instantly align with their persona, active tasks, and execution rules, the repository defines a root-level onboarding configuration:

*   **[.AGENT.md](.AGENT.md)**: The human-readable and agent-facing entry point. It declares the agent's identity as a Lead Systems Programmer, lists its skills directory (`.agent/skills/`), details its task queue (`agent_tasks.md`), and specifies high-priority post-work execution routines.
*   **[.cursorrules](.cursorrules)**: The IDE integration layer that automatically directs modern AI coding tools to read `.AGENT.md` and `.agent/agent.md` upon session startup.

*Note: Due to case-insensitive naming conflicts on Windows between a root file and a directory sharing the name `.agent`, the root-level configuration is named `.AGENT.md` instead of `.AGENT`.*

## Architecture

```mermaid
flowchart LR
    A[".agent/agent.md manifest"] --> B["AgentEngine"]
    A --> C["Runtime entry docs"]
    C --> D["skills.md"]
    C --> E["prompts.md"]
    C --> F["memory.md"]
    C --> G["workflows.md"]
    D --> H["Router"]
    H --> I["Local Python tools"]
    H --> J["MCP tools"]
    H --> K["Claude API skills"]
    F --> L["Memory backends"]
    K --> M["Skill writeback records"]
```

The `.agent/` workspace follows a three-layer model:

1. Manifest: `.agent/agent.md` is the executable source of truth.
2. Entry documents: top-level `.agent/*.md` files are runtime-facing registries
   and contracts.
3. Detailed directories: `.agent/*/` folders hold detailed specs, templates,
   and supporting guidance.



## Repository Layout

```text
.AGENT.md                          Root onboarding entrypoint (Windows compatible)
.cursorrules                       Root IDE / agent bridge
.agent/
  agent.md                         Executable PAP manifest
  skills.md                        Runtime-facing skill registry
  prompts.md                       Prompt registry
  memory.md                        Memory contract
  memory/                          Tiered Memory Storage
    episodic/                      Turn-by-turn history (.jsonl)
    semantic/                      Durable structured knowledge (.json)
    handoff/                       Inter-agent context packets (.json)
    schema.json                    JSON Schema for memory validation
  workflows.md                     Workflow registry

spec/                              Protocol JSON Schema Definitions
  agent-schema.json                JSON Schema for agent.md manifest
  skill-contract.schema.json       JSON Schema for skill contracts
  memory.schema.json               JSON Schema for memory layouts
  workflow.schema.json             JSON Schema for workflows
  knowledge.schema.json            JSON Schema for knowledge base entries

agent_runtime/
  engine.py                        Runtime bootstrap and layout validation
  router.py                        Local, MCP, and Claude API dispatch
  knowledge.py                     Read-only Knowledge Base query interface

  memory/
    __init__.py                    Memory backends
    writeback.py                   Skill execution writeback
tests/                             Pytest coverage for runtime and integrations
```

### Knowledge Base

Durable project knowledge is stored in `.agent/knowledge_base/`. Each entry is
a Markdown file with YAML front-matter (`id`, `title`, `tags`, `created`,
`updated`) validated against `spec/knowledge.schema.json`. An `index.json`
registry file catalogues all entries.

The knowledge base is **read-only at runtime** — any mutation must go through
the T-04 Protocol Evolution process.

## Protocol Schema Validation (`spec/`)

To ensure vendor-agnostic portability and strict structural integrity, the Portable Agent Protocol utilizes standard **JSON Schema (Draft-07)** to formally define and validate all core configuration files.

The schemas are defined under the `spec/` directory:
- **[agent-schema.json](file:///D:/GitHub/Portable-Agent-Protocol/spec/agent-schema.json)**: Standardizes the executable manifest `.agent/agent.md` YAML front-matter (e.g. tools, memory tiers, protocol layout, runtime settings).
- **[skill-contract.schema.json](file:///D:/GitHub/Portable-Agent-Protocol/spec/skill-contract.schema.json)**: Outlines capability contracts in `.agent/skills/*.md`.
- **[memory.schema.json](file:///D:/GitHub/Portable-Agent-Protocol/spec/memory.schema.json)**: Formulates long-term, semantic, episodic, and handoff memory formats.
- **[workflow.schema.json](file:///D:/GitHub/Portable-Agent-Protocol/spec/workflow.schema.json)**: Structures the steps and dependency graphs (DAG) in `.agent/workflows/*.md`.
- **[knowledge.schema.json](file:///D:/GitHub/Portable-Agent-Protocol/spec/knowledge.schema.json)**: Validates front-matter metadata (`id`, `title`, `tags`, `created`, `updated`) for knowledge base entries.

Runtimes validate these layouts automatically during bootstrap. You can trigger manual validation using the CLI:
```bash
python cli.py validate
```


## Installation

```bash
git clone https://github.com/OPluke11-abula/Portable-Agent-Protocol.git
cd Portable-Agent-Protocol
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```



## CLI

The PAP reference CLI provides commands for workspace initialization, schema-enforced validations, skill discovery, memory operations, and workflow runs:

```bash
# Initialize a new .agent/ workspace (interactive)
python cli.py init

# Initialize with explicit flags (non-interactive)
python cli.py init --project-name my-proj --agent-name my-agent --skills search_web,query_db

# Dry-run mode (preview without writing)
python cli.py init --project-name my-proj --agent-name my-agent --dry-run

# Validate the local .agent/ layout and files against schemas
python cli.py validate

# Lint the workspace for schemas, versions, and workflow DAG/dependency consistency
python cli.py lint

# Auto-fix fixable issues
python cli.py lint --fix

# List all declared active skill contracts
python cli.py --list-skills

# Print the detailed schema and contract of a single skill
python cli.py --describe-skill search_web

# Persist and read key-value data using the memory backend
python cli.py --memory-write cli_key "some_value"
python cli.py --memory-read cli_key

# Run an automated multi-step workflow
python cli.py --run-workflow sample_workflow --params '{"arg": 123}'

# Invoke a specific local tool directly
python cli.py --tool search_web --params '{"query":"portable agents"}'

# Search knowledge base entries by keyword
python cli.py --query-knowledge "architecture"

# Retrieve a specific knowledge base entry by ID
python cli.py --get-knowledge api-docs

# Export a signed cross-agent state handoff packet
python cli.py --export-handoff '{"task_state": "Step A done", "pending_steps": ["Do Step B"], "context_summary": "Planning done", "memory_keys": ["data_key"], "handoff_id": "handoff-id"}'

# Import and restore state from a handoff packet file
python cli.py --import-handoff "handoff-id"
```



## Memory

The Python runtime supports:

- `in_memory`
- `local` / `json`
- `sqlite`
- `vector` placeholder backend

The memory package preserves the public import surface:

```python
from agent_runtime.memory import create_memory_backend
from agent_runtime.memory.writeback import write_skill_result
```

## Cross-Agent Handoff

The Portable Agent Protocol includes a robust, schema-validated task handoff mechanism allowing state, context summaries, and memory snapshots to be serialized, signed with SHA-256 integrity checksums, and transferred between different agents cleanly.

- **Export Handoff**: `engine.export_handoff(task_state, pending_steps, context_summary, memory_keys)` packages the state and creates a signed packet file under `.agent/memory/handoff/<handoff_id>.json`.
- **Import Handoff**: `engine.import_handoff(handoff_id)` validates the packet integrity checksum, verifies the schema structure against `spec/memory.schema.json`, and restores the memory snapshot into the target engine's active memory backend.

## MCP Bridge

PAP and MCP solve different layers:

- MCP defines how an agent calls external tools.
- PAP defines how an agent workspace, contracts, prompts, workflows, and memory
  move across environments.

Use:

```bash
python cli.py mcp sync
```

to discover MCP tools and materialize local skill contracts under `.agent/`.

## Validation

Run the standard verification set:

```bash
python -m pytest
python -m compileall cli.py agent_runtime tests
```

The layout tests enforce that `.agent/agent.md`, top-level entry documents, and
detailed protocol directories stay aligned.

## Certification

PAP-compatible runtimes should:

1. Parse `.agent/agent.md` frontmatter.
2. Resolve the declared `.agent/` layout.
3. Preserve the three-layer workspace model.
4. Route declared tools without changing existing public contracts.
5. Pass the conformance and runtime tests in this repository.

See [conformance/CERTIFICATION.md](conformance/CERTIFICATION.md) and the
[LAS integration example](examples/las-integration/).
