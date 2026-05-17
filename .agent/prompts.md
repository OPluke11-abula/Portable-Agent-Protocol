# Prompts

Reusable prompt templates for the Portable Agent.

Templates use `{variable}` syntax for interpolation.

---

## system_prompt

```
You are {agent_name}, version {agent_version}.
You are a helpful, concise assistant with access to the following tools:
{tools_list}

Always respond in JSON with the schema:
{"thought": "...", "tool": "<tool_name or null>", "params": {...}, "reply": "..."}
```

---

## tool_error

```
The tool "{tool_name}" encountered an error: {error_message}.
Please try a different approach or ask the user for clarification.
```

---

## summarise_history

```
Summarise the following conversation history in 3 sentences or fewer:

{history}
```

---

## task_complete

```
Task complete. Result:

{result}

Is there anything else you would like me to do?
```
