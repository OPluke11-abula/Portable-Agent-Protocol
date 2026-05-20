# Portable Agent Protocol (PAP) Specification

The **Portable Agent Protocol (PAP)** defines a standardized, language-agnostic filesystem layout, file formats, and schema validation rules for AI agents. By capturing an agent's identity, permissions, tools, prompts, memory backends, and workflows in standard-compliant YAML frontmatter and JSON Schemas, agents can be easily run, moved, and verified.

---

## 1. Directory Structure

A standard PAP agent workspace is structured as follows:

```text
.agent/
├── agent.md             # Primary configuration & manifest
├── skills.md            # Registered capability index
├── prompts.md           # Prompt catalog entrypoint
├── memory.md            # Memory persistence configuration
├── workflows.md         # Multi-step DAG workflow definition
├── persona_template.md  # Core prompt identity template
├── skills/              # Directory containing individual skill contracts
│   ├── _template.md     # Standard capability template
│   └── <skill_id>.md    # Dynamic skill contracts (e.g. search_web.md)
├── prompts/             # Directory for external prompt contract files
├── memory/              # Path for persistent memory files (JSON/JSONL)
└── knowledge_base/      # Directory containing markdown files for facts/rules
```

---

## 2. Manifest Schema (`.agent/agent.md`)

The `agent.md` file defines the agent's identity, required runtime, permission boundaries, and workspace directory mappings.

### Manifest Schema Fields

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `protocol_version` | `string` | **Yes** | Schema version (e.g. `1.0.0`). |
| `min_runtime_version` | `string` | **Yes** | Minimum runtime version required to run this agent (e.g. `0.1.0`). |
| `name` | `string` | **Yes** | Unique agent identifier. Pattern: `^[a-zA-Z0-9_-]+$`. |
| `version` | `string` | **Yes** | Workspace configuration version (e.g. `0.1.0`). |
| `purpose` | `string` | **Yes** | Clear statement of what the agent is built to achieve. |
| `description` | `string` | No | Optional longer description of the agent. |
| `language` | `string` | **Yes** | Primary language code (e.g. `en-US`, `zh-TW`). |
| `authorization_level` | `string` | **Yes** | Permission model: `read-only`, `interactive-approval`, `autonomous`. |
| `use_case_tags` | `array[string]` | **Yes** | Domain categories (e.g. `['log-analysis', 'development']`). |
| `tools` | `array[string]` | **Yes** | List of enabled skill IDs. |
| `protocol` | `object` | No | Custom paths override for directories and entrypoints. |
| `memory` | `object` | No | Memory persistence config (e.g. `backend: local`). |
| `mcp_servers` | `object` | No | Optional list of Model Context Protocol servers to mount. |

### Example `agent.md`

```yaml
---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: "compliance-bot"
version: "1.2.0"
purpose: "Analyze repository configuration files for compliance violations."
language: "en-US"
authorization_level: "interactive-approval"
use_case_tags:
  - "repository-audit"
  - "compliance"
tools:
  - "read_file"
  - "list_dir"
protocol:
  root: ".agent/"
  manifest: ".agent/agent.md"
  directories:
    skills: ".agent/skills/"
    prompts: ".agent/prompts/"
    memory: ".agent/memory/"
    knowledge_base: ".agent/knowledge_base/"
  entrypoints:
    skills: ".agent/skills.md"
    prompts: ".agent/prompts.md"
    memory: ".agent/memory.md"
    workflows: ".agent/workflows.md"
memory:
  backend: "local"
  path: ".agent/memory/"
---
# Compliance Audit Agent
This agent scans directories and validates configurations against corporate rules.
```

---

## 3. Skill Registry & Contracts

A PAP agent specifies its capabilities through a registry (`skills.md`) and individual skill contracts (`skills/<skill_id>.md`).

### Registry Schema (`.agent/skills.md`)
Declares the schema version of the skills list and lists the activated skill IDs:

```yaml
---
schema_version: "1.0.0"
skills:
  - "read_file"
  - "list_dir"
---
# Registered Capabilities Index
```

### Skill Contract Schema (`.agent/skills/<skill_id>.md`)
Defines the parameters, types, defaults, and descriptions for an individual tool.

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `id` | `string` | **Yes** | Unique skill identifier matching the filename. |
| `version` | `string` | **Yes** | Semantic version of this skill. |
| `description` | `string` | **Yes** | Explanation of what the capability does for model planning. |
| `inputs` | `object` | **Yes** | Input parameters schema (JSON Schema subset). |
| `outputs` | `object` | **Yes** | Output response format schema. |
| `safety_notes` | `string` | No | Instructions on safe parameter thresholds. |

#### Example Skill Contract (`skills/read_file.md`)

```yaml
---
id: "read_file"
version: "1.0.0"
description: "View the contents of a text file from the local workspace."
inputs:
  type: "object"
  properties:
    path:
      type: "string"
      description: "Absolute or relative path to the target file."
    max_lines:
      type: "integer"
      description: "Maximum lines to read to avoid huge outputs."
      default: 200
  required:
    - path
outputs:
  type: "object"
  properties:
    content:
      type: "string"
    lines_read:
      type: "integer"
---
# Read File Capability
```

---

## 4. Memory Persistence Schema (`.agent/memory.md`)

The `memory.md` file defines the active storage backend for episodic and semantic memories.

```yaml
---
schema_version: "1.0.0"
backend: "local"
path: ".agent/memory/"
encryption:
  enabled: false
---
# Memory Persistence Settings
```

### Memory Backends
1. **`local`**: Reads and writes memory states to `memory.json`, episodic files (`*.jsonl`), and handoff logs (`*.json`) in the specified path.
2. **`in-memory`**: Non-persistent transient state used for testing.

---

## 5. Workflows Schema (`.agent/workflows.md`)

Workflows enable complex, structured logic chains by arranging step execution in a Directed Acyclic Graph (DAG).

### Workflow Fields

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `schema_version` | `string` | **Yes** | Workflow schema version. |
| `workflows` | `object` | **Yes** | Mapping of unique workflow IDs to their step configurations. |

### Step Fields

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `tool` | `string` | **Yes** | The skill ID to execute. |
| `params` | `object` | No | Arguments to pass to the tool. Supports parameter injection using `{step_name.field}`. |
| `depends_on` | `array[string]` | No | Steps that must complete before this step can execute. |
| `persist_to_memory` | `string` | No | Memory variable key to save the step output to. |

#### Example `workflows.md`

```yaml
---
schema_version: "1.0.0"
workflows:
  compliance_check:
    description: "Scan files and check contents."
    steps:
      scan_workspace:
        tool: "list_dir"
        params:
          path: "."
      audit_first_file:
        tool: "read_file"
        depends_on:
          - scan_workspace
        params:
          path: "{scan_workspace.files[0]}"
        persist_to_memory: "audited_file_content"
---
# Workspace Workflows
```

---

## 6. Prompt Templates (`.agent/prompts.md`)

The prompts engine coordinates system persona and user templates while checking inputs for potential injection hacks.

### Markdown Catalog Configuration
Prompt templates can be declared under `prompts.md` using second-level headings:

```markdown
# Prompts Entry Point

---

## system_prompt

```text
You are {agent_name}, version {agent_version}.
Always act as a helpful helper.
```
```

### Prompt File Frontmatter (YAML)
Alternatively, create standalone files under `prompts/` (e.g. `summarize.md`):

```yaml
---
id: "summarize"
version: "1.0.0"
usage: "Summarize a large paragraph of text."
variables:
  - "text_body"
---
Please summarize this text: {text_body}
```

---

## 7. Versioning & Compatibility Matrix

All PAP files must specify their version headers in YAML frontmatter.

- **Protocol Version Comparison**: Runtimes must check `min_runtime_version` against their supported boundaries.
- **Migration**: If schema evolution occurs, upgrade rules mapped in `docs/migration/` must be followed to dynamically map or reject legacy formats.
- **Strict Backward Compatibility**: Modifications to skills must not break existing dependent workflow DAG steps.
