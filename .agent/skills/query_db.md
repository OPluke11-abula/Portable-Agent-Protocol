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
