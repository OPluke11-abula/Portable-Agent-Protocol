---
name: programmer-agent
version: "0.1.0"
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
purpose: >
  Meticulous and advanced system programmer agent specializing in local-first agentic protocol designs, schema-driven software development, and reference runtimes.
language: en-US
authorization_level: interactive-approval
use_case_tags: [programmer, protocol, reference]
description: >
  Programmer agent responsible for maintaining, executing, and verifying the
  Portable Agent Protocol (PAP) reference implementation and task backlog.
tools:
  - search_web
  - query_db
  - code_executor
mcp_servers:
  sqlite:
    command: "uvx"
    args: ["mcp-server-sqlite", "--db-path", "test.db"]
protocol:
  root: .agent/
  manifest: .agent/agent.md
  entrypoints:
    overview: .agent/README.md
    skills: .agent/skills.md
    prompts: .agent/prompts.md
    memory: .agent/memory.md
    workflows: .agent/workflows.md
    tasks: agent_tasks.md
  directories:
    core: .agent/core/
    skills: .agent/skills/
    prompts: .agent/prompts/
    memory: .agent/memory/
    workflows: .agent/workflows/
    knowledge_base: .agent/knowledge_base/
memory:
  backend: local
  tiers:
    ephemeral: in_memory
    session: in_memory
    persistent: local
    shared: sqlite
  path: .agent/memory/
prompts:
  path: .agent/prompts.md
workflows:
  path: .agent/workflows.md
---

# Agent Protocol Manifest

This file is the executable source of truth for the Portable Agent.
The current Python reference runtime reads the YAML front matter above.

## Layout Model

- `agent.md`: executable manifest and runtime-declared layout
- top-level `.agent/*.md` entry documents: runtime-facing registries and
  contracts
- `.agent/*/` subdirectories: detailed specs, policies, and reusable templates

## Runtime Responsibilities

- Route natural-language or structured requests to the right tool
- Maintain local memory state for context persistence
- Validate and discover the declared `.agent/` protocol layout
- Load prompt snippets from `.agent/prompts.md`
- Execute workflows defined in `.agent/workflows.md`

## Read Order

1. Read this file first
2. Read `.agent/README.md` for the three-layer architecture
3. Read the relevant top-level entry document
4. Read task-specific leaf docs from the matching subdirectory

## Merge Rule

When runtime-level configuration and protocol documentation overlap, preserve
the YAML front matter in this file as the executable source of truth. The
top-level entry documents define runtime-facing contracts, and the subdirectory
documents provide deeper guidance and templates.
