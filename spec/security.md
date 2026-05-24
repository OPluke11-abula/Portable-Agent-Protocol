# Portable Agent Protocol (PAP) — Security Model & Specifications

This document defines the security architecture, threat model, and standard defensive policies of the Portable Agent Protocol (PAP) runtime environment.

---

## 🔒 1. Threat Model

In an open multi-agent or user-facing agentic environment, the PAP runtime identifies four primary threat vectors:

### Threat A: Prompt Injection (System Prompt Compromise)
- **Vector**: Untrusted variable inputs (e.g. user messages, external search results, document contents) are interpolated directly into highly sensitive `system` or `role` prompts.
- **Risk**: An attacker hijacks the agent's prime directives, forcing it to ignore hard rules, skip validation checks, or run dangerous commands.

### Threat B: Path Traversal (Arbitrary File Resolution)
- **Vector**: Untrusted strings are passed into tool or skill registry lookups (e.g. `skill_id = "../../../etc/passwd"`).
- **Risk**: Unauthorized file access, sensitive configuration leakage, or arbitrary tool loading due to path traversal exploits.

### Threat C: Memory Corruption & Directory Traversal
- **Vector**: Key-value pairs are written to local persistent databases or file paths where the key is polluted (e.g. `key = "../../../session_secrets"` or containing null bytes `\x00`).
- **Risk**: Writing files to arbitrary directories, overwriting critical runtime configurations, or corrupting state persistence.

### Threat D: Unauthorized Tool Execution (Escalation of Privilege)
- **Vector**: A compromised agent automatically calls destructive write-actions (e.g. `code_executor` or `query_db`) without human oversight or system consent.
- **Risk**: Severe data loss, privilege escalation, or shell takeover.

---

## 🛡️ 2. Defensive Mitigation Strategies

To secure the agent environment, PAP implements four core defense layers:

### Layer 1: Prompt Composer escaping and Injection Scans
1. **Dynamic escaping (`escape_prompt_value`)**:
   - Every variable formatted into a `system` or `role` prompt is automatically XML-escaped to neutralize markup-based breakout patterns.
   - All curly braces (`{` and `}`) are double-escaped (`{{` and `}}`) to prevent format-string exploits and nested template injection.
2. **Injection Scanning (`validate_prompt_string`)**:
   - The engine sweeps inputs against known instruction bypass signatures.
   - Variables wrapped explicitly as `SafePromptString` bypass validation, allowing developers to inject trusted, pre-vetted prompts.

### Layer 2: Strict File Verification (`skill_id` Sanitization)
- Every `skill_id` passed to filesystem resolution or contract parsing is strictly checked against the regex pattern `^[a-zA-Z0-9_-]+$`.
- Any character sequence containing path delimiters (`/`, `\\`), parent references (`..`), or special characters is rejected instantly with a `ValueError` before any file operation occurs.

### Layer 3: Memory Key Sandbox Validation
- The base `MemoryBackend` enforces a strict memory key sandbox:
  - Keys must not exceed **256 characters**.
  - Keys must not contain **null bytes** (`\x00`).
  - Keys must not contain directory traversal sequences (`/`, `\\`, `..`).
- Violations trigger an immediate `ValueError`, protecting memory stores across all storage tiers (ephemeral, local JSON, and SQLite).

### Layer 4: Granular Skill Permissions & Autonomy Levels
Every skill call routed through `AgentEngine.call_skill()` is subjected to the three-tier permission model:

| Level | Autonomy Policy | Mitigation / Behavior |
| :--- | :--- | :--- |
| **`auto` / `autonomous`** | Full Autonomy | Skill executes without user interruption. |
| **`interactive-approval`** | Human-in-the-Loop | Invokes a registered `approval_callback` or a TTY stdin prompt. Blocked immediately in non-interactive environments if no callback exists. |
| **`deny`** | Absolute Denial | Directly blocks execution and raises `PermissionError` (standard default for write-skills in `read-only` mode). |

---

## 📈 3. Compliance and Verification

- The local test suite (`tests/test_security.py`) enforces strict validation across all four threat dimensions.
- Every commit must achieve **100% green test passes** and maintain coverage at or above **80%**.
