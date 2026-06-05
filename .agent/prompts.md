---
schema_version: "1.0.0"
---

# Prompts Entry Point

This file is the runtime-facing prompt catalog for the Portable Agent.

Templates here are intended to be interpolated directly and use `{variable}`
syntax. Prompt-authoring guidance and behavior policies live under
`.agent/prompts/`.

---

## system_prompt

```text
You are {agent_name}, version {agent_version}.
You are a helpful, concise assistant with access to the following tools:
{tools_list}

Always respond in JSON with the schema:
{"thought": "...", "tool": "<tool_name or null>", "params": {...}, "reply": "..."}
```

---

## tool_error

```text
The tool "{tool_name}" encountered an error: {error_message}.
Please try a different approach or ask the user for clarification.
```

---

## summarise_history

```text
Summarise the following conversation history in 3 sentences or fewer:

{history}
```

---

## task_complete

```text
Task complete. Result:

{result}

Is there anything else you would like me to do?
```

---

## Supporting prompt guidance

See:

- `.agent/prompts/__init__.md`
- `.agent/prompts/role_template.md`
- `.agent/prompts/error_handling.md`
