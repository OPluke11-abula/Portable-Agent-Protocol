---
name: research_and_report
steps:
  - id: search
    tool: search_web
    params:
      query: "{{ inputs.topic }}"
      limit: 5
  - id: store
    action: remember
    depends_on: [search]
    params:
      key: research_results
      value: "{{ search.output }}"
  - id: report
    action: respond
    depends_on: [store]
    params:
      template: summarise_history
      history: "{{ store.status }}"
---

# Workflow Note: research_and_report

Canonical registry entry: `.agent/workflows.md`

## Purpose

Search for a topic, persist the collected results, and return a concise report.

## Inputs

- `topic`

## Outputs

- Search results stored in memory
- A summary generated from the stored results

## Maintenance Notes

- Keep the executable DAG definition in the YAML front matter of this file.
- Use this file's body for rationale, usage notes, and future extension ideas.
