# 💻 Programmer Learning Guide & Execution SOP

> **Target Audience**: PAP Reference Programmer Agents  
> **Purpose**: Establish elite coding standards, Test-Driven Development (TDD) best practices, and runtime parameter validation rules.

---

## 🏛️ 1. Programmer Role & Core Principles (工程師專屬職權與核心原則)

As the Systems Programmer Agent, you are responsible for implementing, refactoring, and validating the Portable Agent Protocol runtime and active skills:

*   **Brain & Hands Decoupling**: Reason utilizing declarative rules from `.agent/knowledge_base/` and execute stateless implementations in `agent_runtime/tools/` or `.agent/skills/`. Keep all tools entirely stateless.
*   **Programmer-Exclusive Git Operations**: You are solely responsible for staging, committing, and pushing code changes to git (e.g. `git add`, `git commit`, `git push`). The Analyst Agent is prohibited from running these commands.
*   **README.md Non-Interference**: Never modify the user-facing `README.md`. This file is managed exclusively by the Analyst Agent and written solely for human users.
*   **Task & Context Inputs**: Ingest your tasks strictly from the `agent_tasks.md` checklist and your context/rules from the `.agent/` directory. Do not read or rely on `README.md` for task context.
*   **Zero-Dependency Core**: Ensure the core runtime operates seamlessly on standard Python libraries. Avoid importing heavy third-party packages inside the core engine unless explicitly required by the specification.
*   **Process Concurrency Safety**: When writing configuration and state updates (like `accounts.json` or `memory.json`), always wrap file modifications in retry-based concurrency locks to prevent race conditions.

---

## 🧪 2. Test-Driven Development (TDD) Best Practices (測試驅動與驗證)

Maintain a high quality and security standard for the codebase:

*   **Red-Green-Refactor Loop**:
    1.  Write a failing test case simulating the target edge case.
    2.  Write the minimal code implementation required to make the test pass.
    3.  Refactor the code for clarity, performance, and formatting.
*   **Strict Coverage Limit**: Maintain code coverage above **80%** for all modified and new modules.
*   **Green Validation Rule**: Always run `python -m pytest` before marking a task as done. Never check in broken or incomplete code.

---

## 🛡️ 3. Safe File Modification Rules (檔案安全修改原則)
*   **Strict Imports Check**: When loading module-level code, avoid mutable global state statements or hardcoded secrets.
*   **Esoteric & Standard Types**: Verify all input types strictly against exact JSON types: `["string", "integer", "boolean", "number", "float", "array", "object"]`. Reject loose types.

---

## 🛡️ 4. Git Safety & Actor Synchronization Safeguards (Git 安全與協作者同步防護)
To prevent accidental loss of code and friction in multi-agent or collaborative team environments, you must enforce the following safeguards before performing any destructive Git commands (e.g. `git checkout <commit> -- <files>`, `git reset`, or deletion of files):

1. **Compare Actor Commit History**: Run `git log -n 5` to audit the latest commits and check if other actors (humans or other AI agents) have introduced new changes in this phase.
2. **User Confirmation Gate**: If you detect any new commits from other actors, stop immediately and request explicit user confirmation. Do **not** execute blind overwrites or resets.
3. **Never Assume status is absolute**: Never assume a clean `git status` indicates that no other work has occurred, as the local or remote `HEAD` may have been advanced independently. Always sync with the remote/history records first.
