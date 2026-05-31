# .agent Architecture

This `.agent/` workspace is organized in three layers to implement the **LAS Cross-Project Best Practice** and **"Brain & Hands" Decoupling** so the Python runtime and the richer protocol templates can coexist without ambiguity.

---

## 🧠 Brain & Hands Decoupling

- **Brain (Declarative Knowledge / `.agent/knowledge_base/`)**: Houses core domain SOPs, guidelines, and thinking frameworks (e.g. `ai_analyst_learning_guide.md`). These are parsed at runtime to align the agent's cognitive structure.
- **Hands (Reflected Tools / `agent_runtime/tools/` & `.agent/skills/`)**: Houses stateless tools and capability contracts reflected into JSON schemas for programmatic tool-calling.

---

## 🗂️ The Three-Tier Manifest

### Layer 1: Executable Manifest
- **`.agent/agent.md`**: The executable source of truth. The Python reference runtime parses the YAML front matter of this file to discover mounted tools, memory tiers, and protocol paths. It also embeds persona directives and **Hard Rules**.

### Layer 2: Runtime Entry Documents
These top-level files are stable, readable entrypoints for agents and runtimes:
- **`.agent/skills.md`**: Skill registry mapping active tools to their codebase paths and schemas.
- **`.agent/prompts.md`**: Runtime prompt catalog and reusable interpolation snippets.
- **`.agent/memory.md`**: Persistence schema and tiered backend contracts.
- **`.agent/workflows.md`**: Canonical workflow DAG registry.
- **`.agent/routing.md`**: **Situation-to-Skill Selection Rules (情境路由表)** mapping scenarios to specific tools.
- **`.agent/handoff_guide.md`**: **Thread-Hopping Protocol standard operating procedure** and state packet schemas.

### Layer 3: Detailed Protocol Directories
These folders house deep templates, leaf specifications, and persistent assets:
- **`.agent/core/`**: Router, engine, and logger configuration directives.
- **`.agent/skills/`**: Granular PAP capability contracts for local/global overrides.
- **`.agent/prompts/`**: Prompt authoring guides, error handling, thread-hopping templates (`thread_hopping.md`), and detailed scenario routing rules (`situation_routing.md`).
- **`.agent/memory/`**: Epic/session memory records and handoff JSON files.
- **`.agent/workflows/`**: Per-workflow DAG templates and step definitions.
- **`.agent/knowledge_base/`**: Durable declarative project SOPs and guidebooks.
- **`.agent/analyst/`**: Analyst exclusive space, housing logs of lessons learned, thread-sensitive guides, and cognitive thinking templates.
- **`.agent/programmer/`**: Programmer exclusive space, housing programmer coding standards, TDD SOPs, and developer-centric guidelines.

---

## 🛡️ Core Execution Policies

### 1. Onboarding Read Order
Every newly active agent instance must reconstruct 100% state alignment under 0.1 seconds by reading files in this exact order:
$$\text{agent.md (Persona)} \quad \rightarrow \quad \text{skills.md (Tools)} \quad \rightarrow \quad \text{agent\_tasks.md (Tasks/Logs)} \quad \rightarrow \quad \text{handoff\_guide.md (Handoff specs)}$$

### 2. Resolution Pipeline
- If a project-specific skill contract is present in `.agent/skills/<name>.md`, it always **overrides** the global registry.
- Fall back to the Global Skills Registry (`~/.gemini/antigravity/skills/`) when no local override exists.

### 3. Checksum Verification
- State packets exported during thread-hopping must include a SHA-256 integrity checksum. The receiving agent runtime must validate this signature before importing state to prevent data drift or corruption.
