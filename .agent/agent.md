---
name: portable-agent
version: "0.1.0"
description: >
  Reference implementation of the Portable Agent Protocol -
  a minimal, portable runtime for AI collaboration, skills, memory,
  prompts, and self-evolving project workflows.
tools:
  - search_web
  - query_db
  - code_executor
memory:
  backend: local
  path: .agent/memory/
prompts:
  path: .agent/prompts.md
workflows:
  path: .agent/workflows.md
---

# Agent Protocol

This file is the source-of-truth runtime manifest for the Portable Agent.
The YAML front matter above is read by the Python runtime.

## Runtime responsibilities

- Route natural-language or structured requests to the right tool
- Maintain local memory state for context persistence
- Load prompt templates from `.agent/prompts.md`
- Execute workflows defined in `.agent/workflows.md`

## Protocol documentation layers

The runtime manifest lives in this file, but the richer protocol specification is now split across subdirectories:

- `.agent/core/`: engine, router, and logger responsibilities
- `.agent/skills/`: detailed skill contracts and writeback guidance
- `.agent/prompts/`: reusable prompt templates and error-handling patterns
- `.agent/memory/`: short-term and long-term memory notes
- `.agent/knowledge_base/`: static knowledge placeholders and architecture references

## Merge rule

When runtime-level configuration and protocol documentation overlap, preserve the YAML front matter in this file as the executable source of truth, and use the subdirectories for deeper guidance and templates.
