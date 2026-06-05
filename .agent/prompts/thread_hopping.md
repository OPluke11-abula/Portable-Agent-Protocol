---
id: thread_hopping
version: 1.0.0
usage: Executable prompt templates for multi-generational thread-hopping.
variables: []
---
# Thread-Hopping Prompts and Templates

This prompt library defines the executable templates for multi-generational thread-hopping, ensuring seamless context transfer and zero alignment time.

## 📋 A. Re-scan & Blueprint (重新瀏覽與計劃)

Use this prompt when the developer requests a comprehensive project audit, refactoring, or a new feature implementation roadmap.

### Trigger Phrase (Traditional Chinese):
> 「我更新很多東西了，重新瀏覽整個project。我打算讓這個專案，[New Goal]，請重新研究並給我計畫書。」

### System Execution Template (English):
```text
You are triggered in RE-SCAN & BLUEPRINT mode.
1. Sweep the entire codebase recursively (all active workspace roots and .agent directories).
2. Check recent Git log, active diffs, and files modified within the last 7 days.
3. Align with .agent/knowledge_base/ai_analyst_learning_guide.md and core design constraints.
4. Generate a highly detailed, professional English implementation plan in the file:
   `[workspace_root]/implementation_plan.md`
5. Highlight critical architectural decisions, schema modifications, and test coverage requirements.
6. Stop and request explicit developer approval before making any source code edits.
```

## 📋 B. Minimalist Handoff Prompt (精簡提示詞交接)

Use this prompt to condense a complex conversation into a dense, token-efficient packet for the next incoming agent.

### Trigger Phrase (Traditional Chinese):
> 「給專門的agent執行就好，你只要給我提示詞給下一個agnet就好。像是有做那些改動，要做哪些事。」

### System Execution Template (English):
```text
You are triggered in MINIMALIST HANDOFF mode.
1. Scan the current conversation context, tool executions, and intermediate state logs.
2. Prune verbose conversations, raw error stacks, and redundant comments.
3. Generate a structured, high-fidelity English Handoff Prompt inside a code block, formatted as follows:

=== HIGH-FIDELITY AGENT HANDOFF DISPATCH ===
[CONSTRUCTED PERSONA]: Meticulous system programmer specialized in [Topic].
[WHAT CHANGED]: High-level bulleted summary of files added, modified, or deleted.
[CURRENT STATE & BLOCKED ISSUES]: Short status summary.
[INTERFACE CONTRACTS]: Specific inputs/outputs, parameter schemas, and data structures.
[MOCK & TEST REQUIREMENTS]: Specific unit test paths, test assertions, and mock boundaries to prevent redundant API/external calls.
[SECURITY CONSTRAINTS]: Sandbox boundaries, file permission limits, and credentials handling.
[IMMEDIATE TASK LIST]:
  - [ ] Task 1: [Specific description, targets, and precise file paths]
  - [ ] Task 2: ...
[EXIT CRITERIA (DoD)]: Precise verification commands (e.g. pytest command, lint command) and expected outputs.
[CHECKPOINT ID]: handoff_<uuid>
============================================

4. Export the corresponding state payload utilizing `engine.export_handoff(...)`.
```

## 📋 C. Multi-generational Handoff Merge (多代程序員交接整合)

Use this prompt to integrate the outcomes and logs of the preceding generation of programmers with your strategic blueprint.

### Trigger Phrase (Traditional Chinese):
> 「我先給你第 X 代程序員 agent 整理好的東西，等等你就讓你的 Handoff Prompt 跟他結合，整理好後給下一個 agent (程序員)。」

### System Execution Template (English):
```text
You are triggered in MULTI-GENERATIONAL HANDOFF MERGE mode.
1. Parse the outcome packet or prompt block from the "Generation X" programmer agent.
2. Load the current active roadmap from `agent_tasks.md` and the existing blueprint.
3. Resolve any overlapping tasks, duplicated code adjustments, or logic conflicts.
4. Merge the state outcomes and task lists into a single consolidated, seamless queue.
5. Save the updated checklist in `agent_tasks.md` with appropriate completed [x] and pending [ ] items.
6. Generate a unified handoff prompt that guarantees work continuity without introducing context redundancy.
```
