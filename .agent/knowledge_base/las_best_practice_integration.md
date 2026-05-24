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
