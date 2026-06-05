---
id: query_db
name: query_db
description: Query structured data sources through a constrained, auditable database access contract.
version: 1.0.0
inputs:
  connection_target:
    type: string
    description: Named database, MCP server, or runtime-managed data source.
    required: true
  query_intent:
    type: string
    description: Natural-language description of the requested data.
    required: true
  filters:
    type: object
    description: Optional structured filters, limits, or ordering.
    required: false
  safety_constraints:
    type: string
    description: Required access, privacy, or mutation limits.
    required: false
outputs:
  rows:
    type: array
    description: Returned records or an empty list.
  schema_used:
    type: object
    description: Tables, fields, or collections referenced.
  query_summary:
    type: string
    description: Human-readable explanation of what was queried.
  risk_notes:
    type: string
    description: Any access, privacy, performance, or ambiguity concerns.
safety_notes:
  - Default to read-only behavior unless an explicit workflow authorizes writes.
  - Prefer bounded queries and explicit limits.
  - Do not expose secrets or private data beyond the requested scope.
author: pap
---

# Skill: query_db

Query structured data sources through a constrained, auditable database access
contract.

## Purpose

Use this skill when the agent needs to inspect or summarize structured data from
a database-like source. The runtime implementation must keep query intent,
filters, and safety constraints explicit.

## Required Inputs

- `connection_target`: Named database, MCP server, or runtime-managed data
  source.
- `query_intent`: Natural-language description of the requested data.
- `filters`: Optional structured filters, limits, or ordering.
- `safety_constraints`: Required access, privacy, or mutation limits.

## Expected Outputs

- `rows`: Returned records or an empty list.
- `schema_used`: Tables, fields, or collections referenced.
- `query_summary`: Human-readable explanation of what was queried.
- `risk_notes`: Any access, privacy, performance, or ambiguity concerns.

## Safety

- Default to read-only behavior unless an explicit workflow authorizes writes.
- Prefer bounded queries and explicit limits.
- Do not expose secrets or private data beyond the requested scope.
