---
name: programmer-agent
version: 0.1.0
protocol_version: 1.0.0
min_runtime_version: 0.1.0
purpose: 'Meticulous and advanced system programmer agent specializing in local-first
  agentic protocol designs, schema-driven software development, and reference runtimes.

  '
language: en-US
authorization_level: interactive-approval
use_case_tags:
- programmer
- protocol
- reference
description: 'Programmer agent responsible for maintaining, executing, and verifying
  the Portable Agent Protocol (PAP) reference implementation and task backlog.

  '
tools:
- search_web
- query_db
- code_executor
- docx
- llm_api
- pdf
- pptx
- web_artifacts_builder
- xlsx
mcp_servers:
  sqlite:
    command: uvx
    args:
    - mcp-server-sqlite
    - --db-path
    - test.db
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
    routing: .agent/routing.md
    handoff: .agent/handoff_guide.md
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

This file is the executable source of truth for the Portable Agent, incorporating the FindAi Studio **LAS Cross-Project Best Practice** and "Brain & Hands" Decoupling architecture.

## Layout Model (Three-Tier Manifest)

1. **Layer 1: Executable Manifest (`agent.md`)**: Defines metadata, mounted MCP servers, active tools, local memory tiers, and executive routing layout.
2. **Layer 2: Runtime Entry Documents (`.agent/*.md`)**: Stable entrypoints for skills (`skills.md`), prompts (`prompts.md`), memory (`memory.md`), workflows (`workflows.md`), situation routing (`routing.md`), and handoff specifications (`handoff_guide.md`).
3. **Layer 3: Detailed Protocol Directories (`.agent/*/`)**: Hold detailed capability contracts, template fragments, historical memory snapshots, durable declarative domain knowledge, and execution specifications.

## 🛡️ Executive Routing & Hard Rules (最高指導原則與硬限制)

1. **Brain & Hands Decoupling**: Reason utilizing declarative frameworks inside `.agent/knowledge_base/` ("Brain") and execute with stateless reflected Python tools in `agent_runtime/tools/` or custom skills in `.agent/skills/` ("Hands").
2. **Deterministic Routing**: Every incoming request must be routed utilizing the [Situation-to-Skill Selection Rules](file:///d:/GitHub/Portable-Agent-Protocol/.agent/routing.md).
3. **Thread-Hopping Execution**: If the conversation context is bloated or turn-count exceeds 15, immediately trigger [Thread-Hopping Protocol](file:///d:/GitHub/Portable-Agent-Protocol/.agent/handoff_guide.md) to preserve token budget.
4. **Onboarding Read Order**: Newly active agents must ingest documents in this strict order:
   $$\text{agent.md} \quad \rightarrow \quad \text{skills.md} \quad \rightarrow \quad \text{agent\_tasks.md} \quad \rightarrow \quad \text{handoff\_guide.md}$$
5. **Strict 5-Step Work Principles**:
   - **Clean Code**: Remove debug outputs and wrap async operations in try-except blocks.
   - **Service Boundaries**: Decouple core engine, adapters, and tools.
   - **Self-Manifest Update**: Mark completed items in `agent_tasks.md` and document logs.
   - **Bilingual Documentation**: Synchronize English and Chinese sections in `README.md`.
   - **Pre-commit pytest validation**: Always execute pytest suite (`python -m pytest`) to ensure 100% green status before staging and committing.
