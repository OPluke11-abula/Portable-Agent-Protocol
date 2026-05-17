# Workflows

Self-evolving workflow definitions for the Portable Agent.

Each workflow is a named sequence of steps.  Steps map to tool calls or
built-in actions (`respond`, `remember`, `summarise`).

---

## research_and_report

**Description:** Search the web for a topic, store results in memory, then
produce a summary report.

```yaml
name: research_and_report
steps:
  - id: search
    tool: search_web
    params:
      query: "{topic}"
      limit: 5
  - id: store
    action: remember
    params:
      key: research_results
      value: "{search.output}"
  - id: report
    action: respond
    params:
      template: summarise_history
      history: "{store.value}"
```

---

## run_and_explain

**Description:** Execute a code snippet and explain the output.

```yaml
name: run_and_explain
steps:
  - id: execute
    tool: code_executor
    params:
      code: "{code}"
  - id: explain
    action: respond
    params:
      template: task_complete
      result: "{execute.output}"
```

---

## Adding workflows

1. Define a new YAML block in this file with a unique `name`.
2. Reference prompt templates by name in `action: respond` steps.
3. The engine will discover and register the workflow automatically.
