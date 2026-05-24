# Situation-to-Skill Selection Rules (情境路由表)

This document serves as the executable entrypoint for routing situations and developer requests to the correct local or global skills in the Portable Agent Protocol (PAP) environment.

---

## 🔌 Layered Skill Pipeline

We enforce a strict layered resolution pipeline to maximize code reusability while allowing project-level customization:
1. **Local Project Skills (`.agent/skills/` or `skills/`)**: Project-specific capability contracts that override global skills of the same name.
2. **Global Skills Registry (`~/.gemini/antigravity/skills/`)**: Shared, general-purpose fallback skills (e.g. `pdf`, `xlsx`, `docx`, `pptx`, `web_artifacts_builder`).

---

## 🗺️ Selection & Routing Table (情境選擇與路由規則)

The agent must analyze the incoming prompt and user situation, then select the optimal skill based on the rules below:

| Situation / Intent (情境與意圖) | Selected Skill / Action (所選技能與行動) | Routing Logic & Policy (路由邏輯與原則) |
| :--- | :--- | :--- |
| **A. Complex system planning, redesign, or major additions** | **Re-scan & Blueprint (Trigger A)** | Sweep codebase, generate an English `implementation_plan.md` artifact. Stop and wait for approval. |
| **B. Handing off tasks to another agent to save tokens** | **Minimalist Handoff Prompt (Trigger B)** | Prune conversation bloat. Generate dense handoff payload specifying what changed and immediate TODOs. |
| **C. Merging multi-generational agent progress** | **Handoff Merge (Trigger C)** | Combine outcome logs of the previous programmer agent with current strategic blueprint. |
| **D. User requests custom visual UI / web interfaces** | [`web_artifacts_builder`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/web_artifacts_builder.md) | Generate React/Tailwind/shadcn web applications inside a dynamic artifact. |
| **E. Interacting with or testing web apps via Playwright** | `webapp_testing` (Global fallback) | Use browser page snapshotting, evaluate script, fill forms, and check network. |
| **F. User asks for Word document generation / editing** | [`docx`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/docx.md) | Generate formatted report, memo, table of contents, or structured tables. |
| **G. User asks for PowerPoint slide deck or pitch deck** | [`pptx`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/pptx.md) | Create/edit presentation layouts, speaker notes, and templated slide decks. |
| **H. User asks for Excel sheet / CSV parsing / cleaning** | [`xlsx`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/xlsx.md) | Clean tabular data, apply formulas, formatting, and export spreadsheets. |
| **I. Reading, merging, page rotation or OCR on PDFs** | [`pdf`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/pdf.md) | Extract tables, encrypt/decrypt, or OCR PDF documents. |
| **J. Run unit tests, execute scripts, or build system** | [`code_executor`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/code_executor.md) | Run shell commands (e.g. `pytest` or python executions) safely. |
| **K. Accessing databases (SQLite / PostgreSQL)** | [`query_db`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/query_db.md) | Parse database schema, run safe SELECT queries, modify tables. |
| **L. Web search, documentation query, or scrape** | [`search_web`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/search_web.md) | Execute web searches, fetch content, query documentation APIs. |

---

## 🛠️ Override Policy

If a local skill exists in `.agent/skills/<skill_name>.md`, it **MUST** take precedence over the global counterpart. The `Router` module validates calls using the local contract:
- **Local Contract File**: `.agent/skills/<skill_name>.md`
- **Global Skill Path**: `~/.gemini/antigravity/skills/<skill_name>/SKILL.md`

Prevent local parity failures by ignoring global skills during local project validation syncs in `tool_manifest.py`.
