---
id: ai_analyst_learning_guide
title: "LAS Master Architect & Learning Guide for AI Analyst Agents"
tags:
  - las
  - architecture
  - best-practice
created: "2026-05-24"
updated: "2026-05-24"
---
# 🧠 LAS Master Architect & Learning Guide for AI Analyst Agents
> **Target Audience**: AI Analyst Agents across different repositories and domains.  
> **Purpose**: Transfer the elite, highly efficient architectural patterns, handoff protocols, and cognitive strategies engineered in FindAi Studio LLM Agent System (LAS).

---

## 1. 📂 Core Architectural Blueprint: "Brain & Hands" Decoupling

AI Analysts must enforce strict separation between an Agent's reasoning knowledge and its execution capabilities:

* **Brain (Declarative Knowledge / `knowledge_base/`)**: Domain knowledge, SOPs, and thinking frameworks stored in Markdown (`SKILL.md` format) with YAML frontmatter. These are dynamically parsed at runtime and injected into the Jinja2 system prompt context.
* **Hands (Reflected Tools / `skills/`)**: Stateless Python functions whose first argument is a Pydantic `BaseModel`. The engine dynamically reflects these models into JSON schemas for tool-calling.
* **Local Workspace Contract (`.agent/`)**: The PAP-compliant workspace contract containing:
  - `agent.md`: The Persona, Hard Rules, and Executive routing rules.
  - `agent_tasks.md`: The active checklist, progression tracking, and merged outcome logs.
  - `skills/`: Project-specific capability contracts.

---

## 🔄 2. Multi-Generational Thread Handoff Protocol (Thread-Hopping)

To prevent LLM context drift, attention decay, and token budget explosion during long-running tasks, you must actively guide the developer to hop threads.

```
Long-Turn Session (Drift & Bloat) ➔ Export Handoff Packet ➔ Spawn Clean Thread ➔ Ingest Packet ➔ Warm Start
```

### The Onboarding Sequence:
Every newly spawned Agent must read files in this exact order to reconstruct 100% state alignment under 0.1 seconds:
$$\text{agent.md (Persona)} \quad \rightarrow \quad \text{skills.md (Tools)} \quad \rightarrow \quad \text{agent_tasks.md (Tasks/Logs)} \quad \rightarrow \quad \text{handoff\_guide.md (Handoff specs)}$$

### Standard Prompt Templates for the Analyst Agent:

#### A. Re-scan & Blueprint (重新瀏覽與計劃)
* **Trigger Prompt**: *"我更新很多東西了，重新瀏覽整個project。我打算讓這個專案，[New Goal]，請重新研究並給我計畫書。"*
* **Action**: Sweep the codebase recursively, read recent commits/diffs, and generate a detailed English `implementation_plan.md`.

#### B. Minimalist Handoff Prompt (精簡提示詞交接)
* **Trigger Prompt**: *"給專門的agent執行就好，你只要給我提示詞給下一個agnet就好。像是有做那些改動，要做哪些事。"*
* **Action**: Prune verbose commentary. Generate a highly dense **English Handoff Prompt** containing exactly what changed, the programmer persona, and the immediate tasks list.

#### C. Multi-generational Handoff Merge (多代程序員交接整合)
* **Trigger Prompt**: *"我先給你第 X 代程序員 agent 整理好的東西，等等你就讓你的 Handoff Prompt 跟他結合，整理好後給下一個 agent (程序員)。"*
* **Action**: Merge the outcome/outcome logs of the previous Programmer Agent with your strategic blueprint, ensuring seamless work continuity without context redundancy.

---

## 🔌 3. Layered Skill Pipeline (Global/Local Overrides)

To maximize code reusability and eliminate redundant file copies across projects, implement a layered resolution path:

* **Global Skills Registry (`~/.gemini/antigravity/skills/`)**: Shared, general-purpose Markdown skills (e.g. `pdf`, `xlsx`, `docx`, `pptx`, `web-artifacts-builder`).
* **Local Skills Registry (`.agent/skills/` or `skills/`)**: Project-specific skills that can complement or directly **override** global skills of the same name.
* **Resolution Pipeline**:
  $$\text{Local Project Skills } \rightarrow \text{ Global Skills fallback}$$
* **Validation Separation**: Prevent local parity check failures by configuring `tool_manifest.py` to identify and ignore global skills during local project syncs/validations.

---

## ⛓️ 4. Deterministic Dynamic Execution (n8n-like Workflows)

Unbounded agent swarms are dangerous and expensive. Restrict complex multi-step tasks to a deterministic state machine:

* **Declarative DAG Steps**: Define workflows under `.agent/workflows/<id>.md` as node-based DAG steps.
* **JSON Payload Passing**: Automatically map outcomes of a step to inputs of the next step via structured template tags (e.g., `{{steps.name.output}}`).
* **Checkpointing & Non-Destructive Resuming**: Save state into `runs/<session_id>.json`. If step $N$ fails, the developer fixes the bug and runs `--resume`, continuing exactly from step $N$ without re-running steps $1 \rightarrow N-1$, saving massive amounts of tokens.

---

## 📊 5. Token Auditing & Auto-Failover Ecosystem

* **Thread-Safe Account Storage**: Keep API credentials, models, and token statistics in `accounts.json` under concurrency locks.
* **Real-time Auditing**: Hook LLM provider callbacks to immediately update `prompt_tokens`, `completion_tokens`, and `total_tokens` on every completion or stream chunk.
* **Failover Protocol**: Immediately check the active account's remaining token budget before calling an LLM. If the budget is exceeded, automatically failover to the next available provider account to protect the developer's vibe coding.

---

## ⚠️ 6. Strict 5-Step Work Principles (每次任務完成自我檢核)

Every time an execution Agent completes a task, it must strictly execute these steps before concluding its turn:

1. **Clean Code & Bugs**: Clean unused imports, delete print/debug statements, and wrap async calls in robust try-except catch blocks.
2. **Framework Decoupling**: Ensure clean service boundaries are maintained between engine, skills, routers, and adapters.
3. **Self-Manifest Update & Compaction**: Automatically mark completed checklists in `agent_tasks.md`, append outcome logs, and **compact completed phases/tasks every 5 to 15 turns**.
4. **Analyst-Exclusive README.md Management**: Only the Analyst Agent is authorized to modify the user-facing `README.md` for human readability.
5. **Programmer-Exclusive Git Operations**: Only the Programmer Agent is authorized to execute git stage, commit, and push commands.
6. **Git Pre-commit Validation**: Run the pytest suite to ensure 100% green light prior to the Programmer staging and committing changes.

---

## 🧠 7. Context-Length Optimization & Cognitive Hygiene (上下文優化與認知衛生)

AI Analysts must actively practice cognitive hygiene to preserve context window reasoning quality across multi-generational turns:

1. **Active Compaction (Every 5-15 Turns)**: When executing plans, compact completed phases inside `agent_tasks.md` into dense, tabular milestones. A clean, compact checklist reduces cognitive distraction and model hallucinations.
2. **Thread-Hopping Rotation (Every 5-15 Turns)**: Trigger thread-hopping transitions every 5 to 15 turns by generating a comprehensive **English handoff prompt** and handing over to a clean agent instance to maintain high-quality reasoning.
3. **Exclusive README.md Management**: Maintain the user-facing `README.md` solely for human users. Agents must read their execution context from `.agent/`, never relying on `README.md`. Technical developer lists or thread-hopping logs must **never** be placed in `README.md`.
4. **Workspace Pruning**: Guide the Programmer to regularly delete untracked temporary outputs, execution logs, and coverage databases (`.coverage`). Keeping the workspace clean prevents file context noise.
5. **Strict Cognitive Isolation**: Enforce distinct boundary files for self-reflections (e.g., `analyst/lessons_learned.md` vs. `programmer/lessons_learned.md`) to prevent persona confusion and maintain high role-specific prompt effectiveness.
