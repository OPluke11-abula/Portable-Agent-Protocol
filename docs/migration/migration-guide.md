# Version Migration & Schema Evolution Guide

As the Portable Agent Protocol (PAP) ecosystem grows, upgrading agent manifests, skill contracts, and workflows to conform to the latest standard specs is critical to maintaining type safety and multi-agent interoperability.

This guide details the upgrade paths, schema modifications, and backward-compatibility guardrails for migrating workspaces.

---

## 1. Upgrading from v0.1.0 to v1.0.0

The transition from the **v0.1.0 (Initial Draft)** to the **v1.0.0 (Official Standard)** represents the formalization of schemas and directories.

### Key Changes Summary

| Component | In v0.1.0 (Draft) | In v1.0.0 (Standard) | Action Required |
| :--- | :--- | :--- | :--- |
| **Manifest YAML** | Unvalidated frontmatter | Enforced by `agent-schema.json` | Add `protocol_version` and `min_runtime_version` headers. |
| **Registry** | Simple tool array | Structured `skills.md` with schema version | Scaffold registry frontmatter in `.agent/skills.md`. |
| **Skill Contracts** | Multi-vendor variations | Vendor-agnostic formats | Standardize inputs/outputs using strict JSON Schema subtypes. |
| **Memory folders** | Ad-hoc `memory/` path | Standard `episodic/`, `semantic/`, and `handoff/` subfolders | Scaffold subdirectories; configure path in `agent.md`. |
| **Workflows** | Custom lists | Standard DAG step schemas | Standardize on `{step_name.field}` brackets for parameter mapping. |

---

## 2. Upgrading Your Workspace Step-by-Step

Follow these steps to upgrade an existing v0.1.0 agent workspace to the v1.0.0 standard.

### Step 1: Standardize the Agent Manifest (`.agent/agent.md`)
Add required standard headers to your YAML frontmatter. Ensure the `name` only contains standard alphanumeric characters, dashes, or underscores.

**Before (v0.1.0):**
```yaml
---
agent-name: "My Legacy Agent"
purpose: "Scraping webpages"
enabled_tools: ["search_web"]
---
```

**After (v1.0.0):**
```yaml
---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: "my-legacy-agent"
version: "1.0.0"
purpose: "Scrape web pages and parse markdown."
language: "en-US"
authorization_level: "interactive-approval"
use_case_tags:
  - "web-scraping"
tools:
  - "search_web"
---
```

### Step 2: Establish the Registry Catalog (`.agent/skills.md`)
Wrap legacy capability listings into a standard frontmatter structure specifying `schema_version`.

**Before (v0.1.0):**
```markdown
# Skills Index
- search_web
```

**After (v1.0.0):**
```yaml
---
schema_version: "1.0.0"
skills:
  - "search_web"
---
# Registered Capabilities Index
```

### Step 3: Remove Vendor Lock-Ins from Skill Contracts (`skills/*.md`)
Ensure that your skill descriptions and parameter naming do not reference specific AI models or vendor features (e.g. "for Claude Code", "OpenAI formatting rules"). Ensure schemas only utilize valid JSON Schema specifications:

**Before (v0.1.0):**
```yaml
---
id: "search_web"
inputs:
  - name: "query"
    type: "str"
    openai_format: true
---
```

**After (v1.0.0):**
```yaml
---
id: "search_web"
version: "1.0.0"
description: "Perform a search query using search engines."
inputs:
  type: "object"
  properties:
    query:
      type: "string"
      description: "Search keyword."
  required:
    - query
outputs:
  type: "object"
  properties:
    results:
      type: "array"
      items:
        type: "object"
---
```

### Step 4: Initialize Memory Subfolders
Scaffold the standard subdirectory tree to enable episodic event logging and multi-agent handoffs:

```bash
mkdir -p .agent/memory/episodic
mkdir -p .agent/memory/semantic
mkdir -p .agent/memory/handoff
```

---

## 3. Forward & Backward Compatibility Rules

To ensure stable agent execution across distributed orchestrations:

- **Strict Backward Compatibility**: A newer runtime must be able to load and execute an older workspace config as long as the workspace specifies a valid `protocol_version` compatible with the runtime boundaries.
- **Breaking Skill Mutation Restrictions**: When mutating or adding new capabilities:
  - Changing an input parameter from *optional* to *required* is considered a **breaking change** and must trigger a major version upgrade.
  - Adding a new *optional* parameter is considered **backward-compatible**.
- **Automated Validation Guard**: Always run the lint verification hook prior to execution:
  ```bash
  python cli.py lint
  ```
