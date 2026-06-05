---
id: search_web
name: search_web
description: Search trusted web sources and return cited, confidence-scored summaries.
version: 1.0.0
inputs:
  query:
    type: string
    description: Search query or research question.
    required: true
  time_scope:
    type: string
    description: Optional recency window or date constraint.
    required: false
  preferred_sources:
    type: array
    description: Optional list of source domains or source types.
    required: false
  must_cite:
    type: boolean
    description: Whether the result must include source URLs.
    required: false
outputs:
  summary:
    type: string
    description: Concise answer or research synthesis.
  sources:
    type: array
    description: Source records with title, URL, and snippet when available.
  confidence:
    type: string
    description: Qualitative confidence level.
  open_questions:
    type: array
    description: Gaps or unresolved follow-up questions.
safety_notes:
  - Prefer primary or official sources for technical, legal, medical, or financial claims.
  - Do not invent citations.
  - Mark stale, uncertain, or unverified information clearly.
author: pap
---

# Skill: search_web

Search trusted web sources and return cited, confidence-scored summaries.

## Purpose

Use this skill when a task needs current, source-backed information from the
web. The runtime implementation may use a stub, a search API, or a host-provided
browser/search tool, but the contract stays stable across runtimes.

## Required Inputs

- `query`: Search query or research question.
- `time_scope`: Optional recency window or date constraint.
- `preferred_sources`: Optional list of source domains or source types.
- `must_cite`: Whether the result must include source URLs.

## Expected Outputs

- `summary`: Concise answer or research synthesis.
- `sources`: Source records with title, URL, and snippet when available.
- `confidence`: Qualitative confidence level.
- `open_questions`: Gaps or unresolved follow-up questions.

## Safety

- Prefer primary or official sources for technical, legal, medical, or financial
  claims.
- Do not invent citations.
- Mark stale, uncertain, or unverified information clearly.
