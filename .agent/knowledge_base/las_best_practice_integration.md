---
id: las_best_practice_integration
title: "LAS Best Practice Integration & Implementation Blueprint"
tags:
  - las
  - architecture
  - integration-guide
created: "2026-05-24"
updated: "2026-05-24"
---
# 🧠 LAS Best Practice Integration & Implementation Blueprint
> **Analyst Onboarding Instruction Prompt**:
> "Please first read and understand the `ai_analyst_learning_guide.md` handbook. This is our newly engineered LAS cross-project best practice. Take this architecture as the supreme guiding principle to design a Three-Tier Manifest (.agent/), Situation-to-Skill Selection Rules, and Thread-Hopping Protocol for this project!"

---

## 📂 1. "Brain & Hands" Decoupling Implementation

To ensure maximum reasoning consistency and minimize token attention decay for AI agents, the project structure must enforce strict physical and logical decoupling:

* **Brain (Declarative Knowledge - Read-Only)**:
  - All local cognitive contexts and declarative frameworks must be stored exclusively inside the `.agent/knowledge_base/` directory.
  - **Schema Validation Constraint**: Every markdown knowledge entry must begin with a valid YAML front-matter conforming to `spec/knowledge.schema.json`:
    ```yaml
    id: machine_readable_id
    title: "Human-Readable Title"
    tags: [las, integration]
    created: "YYYY-MM-DD"
    updated: "YYYY-MM-DD"
    ```
* **Hands (Stateless Reflected Tools)**:
  - The tool execution layer (e.g., `agent_runtime/tools/`) must remain entirely stateless, accepting inputs and returning outputs.
  - Implement a Local-over-Global resolution pipeline: project-local skill contracts (`.agent/skills/<name>.md`) take absolute precedence and directly override global registry fallbacks.

---

## 🗂️ 2. Three-Tier Manifest Model (.agent/)

To eliminate conflicts when running active runtime configs alongside extensive cognitive prompts, the workspace is structured into a Three-Tier Manifest layout:

1. **Layer 1: Executable Manifest (`.agent/agent.md`)**:
   - The single source of truth containing YAML front-matter declaring metadata, mounted MCP servers, active `tools`, and `protocol.entrypoints`.
   - Embeds the **Hard Rules & Executive Routing Directives** to govern all runtime operations.
2. **Layer 2: Runtime Entry Documents (`.agent/*.md`)**:
   - **`routing.md`**: The formal **Situation-to-Skill Selection Rules (情境路由表)** mapping user situations to target tools.
   - **`handoff_guide.md`**: The **Thread-Hopping Protocol standard operating procedure (SOP)** and Handoff Packet schemas.
3. **Layer 3: Detailed Prompt & Template Registries (`.agent/prompts/` etc.)**:
   - House highly granular prompt snippet contracts with strict schema YAML headers:
     - `thread_hopping.md`: Prompt templates for **Trigger A (Re-scan & Blueprint)**, **Trigger B (Minimalist Handoff)**, and **Trigger C (Multi-generational Handoff Merge)**.
     - `situation_routing.md`: Execution guidelines for visual UI development, Office document generation, handoff logic, and test suite verification.

---

## 🗺️ 3. Situation-to-Skill Selection Rules (情境路由表)

When receiving user requests, the Analyst Agent must precisely analyze the intent and dispatch it using the routing matrix:

| Situation / Intent | Selected Skill / Action | Routing Logic & Policy |
| :--- | :--- | :--- |
| **A. Complex system planning, redesign, or major additions** | **Re-scan & Blueprint (Trigger A)** | Recursively sweep the workspace, generate `implementation_plan.md`, and stop for human approval. |
| **B. Handing off tasks to another agent to save tokens** | **Minimalist Handoff Prompt (Trigger B)** | Prune conversation logs. Generate a dense handoff packet with a SHA-256 integrity checksum. |
| **C. Merging multi-generational agent progress** | **Handoff Merge (Trigger C)** | Combine outcome logs of the previous programmer agent with current active roadmap in `agent_tasks.md`. |
| **D. User requests custom visual UI / web interfaces** | `web_artifacts_builder` (Local/Global) | Generate React/Tailwind/shadcn web applications inside a dynamic artifact. Avoid using placeholders. |
| **E. Run unit tests, execute scripts, or build system** | `code_executor` | Execute shell commands (e.g., `pytest`) and stream the output in real-time. |

---

## 🔄 4. Multi-Generational Thread-Hopping Protocol

When conversation context bloats (exceeding 32k tokens) or turn-count exceeds 15, trigger clean-thread hopping:

* **Strict Onboarding Read Order (Cognitive Warm Start)**:
  $$\text{agent.md (Persona)} \quad \rightarrow \quad \text{skills.md (Tools)} \quad \rightarrow \quad \text{agent\_tasks.md (Tasks/Logs)} \quad \rightarrow \quad \text{handoff\_guide.md (SOP)}$$
* **Integrity Checksum Validation**:
  - Handoff packets exported dynamically using the engine's built-in handoff routines must contain a **SHA-256 Checksum** signature over the canonical JSON payload.
  - The receiving agent's runtime must validate this signature before importing state to prevent context corruption or partial transfer failures.
  
---

## ⚠️ 5. Test-Driven Compliance & Self-Evolution (自我演進)

* **100% Green Light Rule**:
  - Every single code modification must be verified by running the local test suite prior to staging (`git add .`):
    `C:\Users\luke2\AppData\Local\Programs\Python\Python314\python.exe -m pytest`
* **Proactive Task Queue Evolution**:
  - The Analyst Agent must continuously audit the codebase against the LAS Guide, proactively appending new high-value engineering tasks (e.g., Decoupling Linter, Strict Onboarding Verifier, Auto-Failover) to `agent_tasks.md`, dynamically updating the Task Summary statistics.

---

## 🧠 6. Context-Length Optimization & Cognitive Hygiene (上下文優化與認知衛生)

To maximize reasoning efficiency, prevent context decay, and avoid model hallucinations during multi-generational long-running threads, the protocol enforces strict context-length optimization standards:

* **Task Registry Compaction (任務清單濃縮)**:
  - **Every 5 to 15 turns**, the agent must actively review and compact the completed tasks/phases inside `agent_tasks.md` into a dense, high-density milestone summary table.
  - This prevents the active context window from being cluttered with hundreds of lines of static `[x]` items, saving up to 75% of context token overhead.
* **Thread-Hopping Rotation (5-15 Turn Handover)**:
  - **Every 5 to 15 turns**, the active agent must trigger thread-hopping by exporting the session state and passing task execution to a clean agent instance.
  - The handover must be accompanied by a **complete English handoff prompt** specifying exact status and immediate action items.
* **Analyst Boundary Control Gate (分析師邊界管制)**:
  - Strict enforcement of Systems Analyst and Software Architect boundaries. Prioritize high-level architecture design, schema contracts, cost-accounting reviews, and security gate audits. Do not proceed to codebase execution or modification unless explicitly instructed by the user. Always wait for user confirmation on plans before dispatching programmer tasks.
* **High-Fidelity Prompt Delegation (高保真提示詞委派)**:
  - Avoid writing brief or generic task descriptions during handovers or multi-agent swarms. Enforce structural delegation prompts containing:
    1. Input/Output schemas and interface contracts.
    2. Mock and test requirements (to restrict redundant API costs/external dependencies).
    3. Sandboxed security limits (file access, network scopes).
    4. Exact file scopes and precise exit criteria (DoD).
* **Exclusive README.md Management & Intended Audience**:
  - The user-facing `README.md` is updated exclusively by the Analyst Agent.
  - **Human Audience ONLY**: `README.md` is intended solely for human users, not for agents. Agents must ingest their guidelines and schemas exclusively from `.agent/` directory entry points, never relying on `README.md`.
  - **No Developer Overhead**: Technical checklists, internal progress logs, and multi-generational thread records must **never** be placed in the user-facing `README.md`.
* **Programmer-Exclusive Git Delegation**:
  - Staging, committing, and pushing code changes to git (e.g. `git add`, `git commit`, `git push`) are executed exclusively by the Programmer Agent (representing the stateless execution "Hands").
  - The Analyst Agent is strictly prohibited from running git commit/push operations.
* **Context-Length Pruning (專案檔案裁剪)**:
  - Proactively delete temporary test databases, coverage caches (e.g., `.coverage`), build artifacts, and standard interpreter cache directories (e.g., `.pytest_cache/`, `__pycache__/`) from the active workspace.
  - Never feed temporary/untracked logs or coverage files to the LLM context.
* **Role-Isolated Reflection Logs (角色隔離日誌)**:
  - Self-reflection records, lessons learned, and prompt guide improvements must be partitioned strictly by roles into `.agent/analyst/` and `.agent/programmer/` respectively.
  - This maintains logical reasoning boundaries and prevents prompt pollution between the architect (Analyst) and implementation (Programmer) minds.
