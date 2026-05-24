---
id: situation_routing
version: 1.0.0
usage: Granular situation-to-skill selection rules and prompt context fragments.
variables: []
---
# Granular Situation-to-Skill Selection Rules (情境路由細則)

This prompt catalog provides specific execution instructions and cognitive boundaries when matching user situations to appropriate skills.

## 🎯 1. Scenario: Advanced Web Interface / UI Development

### Situation:
The user wants a modern, highly interactive web tool, visual dashboard, prototype, or complex frontend application.

### Active Instruction:
- **Routing Decision**: Route to [`web_artifacts_builder`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/web_artifacts_builder.md) (Global/Local) or `frontend_design`.
- **Cognitive Rule**: Do **NOT** write simple, minimal viable products or standard plain HTML pages unless explicitly requested. Always utilize vibrant colors, harmonized HSL tailoring, smooth gradients, and micro-animations.
- **Safety Rule**: If images or external assets are required, use `generate_image` tool directly to supply real assets. Do **NOT** use placeholder links (e.g. `placeholder.com`).

## 🎯 2. Scenario: Data Processing & Document Creation (Office Suite)

### Situation:
The user asks to process tables, clean data columns, or output a report, slide deck, or memo as an Office document format (`.xlsx`, `.pptx`, `.docx`, `.pdf`).

### Active Instruction:
- **Routing Decision**: Match to specific skills:
  - Tabular manipulation ➔ [`xlsx`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/xlsx.md)
  - Presentations / Pitch decks ➔ [`pptx`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/pptx.md)
  - Word documents / Memos ➔ [`docx`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/docx.md)
  - PDF reading, merging, or OCR ➔ [`pdf`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/pdf.md)
- **Cognitive Rule**: Maintain clean service boundaries. Never mix processing logic with UI logic. When generating a slide deck, use professional styling libraries or the built-in theme factories rather than raw ad-hoc styles.

## 🎯 3. Scenario: Cognitive Handoff & Memory Consolidation

### Situation:
The active session has reached turn count limit, token usage is close to 32k, or attention decay is observed in intermediate agent actions.

### Active Instruction:
- **Routing Decision**: Execute the **Thread-Hopping Sequence** (Onboarding sequence 1 to 4).
- **Cognitive Rule**: Strictly follow the Onboarding Order:
  $$\text{agent.md} \quad \rightarrow \quad \text{skills.md} \quad \rightarrow \quad \text{agent\_tasks.md} \quad \rightarrow \quad \text{handoff\_guide.md}$$
- **Verification Rule**: Verify the checksum integrity signature before accepting or parsing any historical handoff state.

## 🎯 4. Scenario: Core Engine Refactoring & Pytest Verification

### Situation:
The user requests a modification to `agent_runtime` or core routing files.

### Active Instruction:
- **Routing Decision**: Execute [`code_executor`](file:///d:/GitHub/Portable-Agent-Protocol/.agent/skills/code_executor.md) to run pytest.
- **Hard Rule**: The project MUST maintain 100% test compliance. Every code modification must be verified by running the local test suite using:
  `C:\Users\luke2\AppData\Local\Programs\Python\Python314\python.exe -m pytest` or `pytest`
