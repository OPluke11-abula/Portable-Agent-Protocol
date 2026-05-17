---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: "LAS_Assistant"
version: "1.0.0"
purpose: "A lightweight assistant powered by LAS and configured by PAP."
language: "en"
authorization_level: "read_only"
use_case_tags:
  - las
  - demo
memory:
  backend: "local"
  path: ".agent/memory/"
layout:
  persona: ".agent/persona.md"
  memory: ".agent/memory.md"
  workflows: ".agent/workflows.md"
  skills_dir: ".agent/skills/"
tools:
  - "search_web"
  - "read_file"
---

# LAS_Assistant Manifest
This directory serves as the configuration payload for a LAS-driven agent.
