---
schema_version: "1.0.0"
---

# Workflow Registry

This file is the canonical runtime-facing workflow registry for the Portable Agent.

Each workflow is defined in its respective `.agent/workflows/<workflow_name>.md` file using YAML front matter. Workflows are executed as Directed Acyclic Graphs (DAGs).

---

## Registered Workflows

- **`research_and_report`**: Search the web for a topic, store results in memory, then produce a summary report.
- **`run_and_explain`**: Execute a code snippet and explain the output.

---

## Adding workflows

1. Create a new markdown file in `.agent/workflows/` (e.g., `my_workflow.md`).
2. Define the execution DAG in the YAML front matter using `steps` and `depends_on`.
3. Use string interpolation like `{{ step_id.output }}` to pass data between steps.
4. Update this `workflows.md` index file for documentation purposes.

---

## Detailed workflow notes

See:

- `.agent/workflows/__init__.md`
- `.agent/workflows/research_and_report.md`
- `.agent/workflows/run_and_explain.md`
