---
schema_version: "1.0.0"
---

# Skills Entry Point

This file is the runtime-facing skill registry for the Portable Agent.

Use it to map tool names to Python modules or external Anthropic skill
sources. Detailed per-skill PAP contracts live in `.agent/skills/*.md`.

## Runtime skill registry

- name: algorithmic_art
  description: Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use this when users request creating art using code, generative art, algorithmic art, flow fields, or particle systems. Create original algorithmic art rather than copying existing artists' work to avoid copyright violations.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/algorithmic-art/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/algorithmic-art/SKILL.md
- name: brand_guidelines
  description: Applies Anthropic's official brand colors and typography to any sort of artifact that may benefit from having Anthropic's look-and-feel. Use it when brand colors or style guidelines, visual formatting, or company design standards apply.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/brand-guidelines/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/brand-guidelines/SKILL.md
- name: canvas_design
  description: Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the user asks to create a poster, piece of art, design, or other static piece. Create original visual designs, never copying existing artists' work to avoid copyright violations.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/canvas-design/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/canvas-design/SKILL.md
- name: claude_api
  description: Build, debug, and optimize Claude API / Anthropic SDK apps. Apps built with this skill should include prompt caching. Also handles migrating existing Claude API code between Claude model versions (4.5 → 4.6, 4.6 → 4.7, retired-model replacements). TRIGGER when: code imports `anthropic`/`@anthropic-ai/sdk`; user asks for the Claude API, Anthropic SDK, or Managed Agents; user adds/modifies/tunes a Claude feature (caching, thinking, compaction, tool use, batch, files, citations, memory) or model (Opus/Sonnet/Haiku) in a file; questions about prompt caching / cache hit rate in an Anthropic SDK project. SKIP: file imports `openai`/other-provider SDK, filename like `*-openai.py`/`*-generic.py`, provider-neutral code, general programming/ML.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/claude-api/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/claude-api/SKILL.md
- name: code_executor
  description: Local PAP runtime skill code_executor.
  source: pap
  source_path: agent_runtime/tools/code_executor.py
  anthropic_compatible: true
  pap_contract_path: .agent/skills/code_executor.md
  anthropic_skill_path: ./anthropic_skills/code-executor/SKILL.md
- name: doc_coauthoring
  description: Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content. This workflow helps users efficiently transfer context, refine content through iteration, and verify the doc works for readers. Trigger when user mentions writing docs, creating proposals, drafting specs, or similar documentation tasks.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/doc-coauthoring/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/doc-coauthoring/SKILL.md
- name: docx
  description: Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Triggers include: any mention of 'Word doc', 'word document', '.docx', or requests to produce professional documents with formatting like tables of contents, headings, page numbers, or letterheads. Also use when extracting or reorganizing content from .docx files, inserting or replacing images in documents, performing find-and-replace in Word files, working with tracked changes or comments, or converting content into a polished Word document. If the user asks for a 'report', 'memo', 'letter', 'template', or similar deliverable as a Word or .docx file, use this skill. Do NOT use for PDFs, spreadsheets, Google Docs, or general coding tasks unrelated to document generation.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/docx/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/docx/SKILL.md
- name: frontend_design
  description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/frontend-design/SKILL.md
- name: internal_comms
  description: A set of resources to help me write all kinds of internal communications, using the formats that my company likes to use. Claude should use this skill whenever asked to write some sort of internal communications (status reports, leadership updates, 3P updates, company newsletters, FAQs, incident reports, project updates, etc.).
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/internal-comms/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/internal-comms/SKILL.md
- name: mcp_builder
  description: Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/mcp-builder/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/mcp-builder/SKILL.md
- name: pdf
  description: Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce one, use this skill.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/pdf/SKILL.md
- name: pptx
  description: Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx filename, regardless of what they plan to do with the content afterward. If a .pptx file needs to be opened, created, or touched, use this skill.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/pptx/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/pptx/SKILL.md
- name: query_db
  description: Local PAP runtime skill query_db.
  source: pap
  source_path: agent_runtime/tools/query_db.py
  anthropic_compatible: true
  pap_contract_path: .agent/skills/query_db.md
  anthropic_skill_path: ./anthropic_skills/query-db/SKILL.md
- name: search_web
  description: Local PAP runtime skill search_web.
  source: pap
  source_path: agent_runtime/tools/search_web.py
  anthropic_compatible: true
  pap_contract_path: .agent/skills/search_web.md
  anthropic_skill_path: ./anthropic_skills/search-web/SKILL.md
- name: skill_creator
  description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/skill-creator/SKILL.md
- name: slack_gif_creator
  description: Knowledge and utilities for creating animated GIFs optimized for Slack. Provides constraints, validation tools, and animation concepts. Use when users request animated GIFs for Slack like "make me a GIF of X doing Y for Slack.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/slack-gif-creator/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/slack-gif-creator/SKILL.md
- name: theme_factory
  description: Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifact that has been creating, or can generate a new theme on-the-fly.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/theme-factory/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/theme-factory/SKILL.md
- name: web_artifacts_builder
  description: Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex artifacts requiring state management, routing, or shadcn/ui components - not for simple single-file HTML/JSX artifacts.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/web-artifacts-builder/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/web-artifacts-builder/SKILL.md
- name: webapp_testing
  description: Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/webapp-testing/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/webapp-testing/SKILL.md
- name: xlsx
  description: Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing .xlsx, .xlsm, .csv, or .tsv file (e.g., adding columns, computing formulas, formatting, charting, cleaning messy data); create a new spreadsheet from scratch or from other data sources; or convert between tabular file formats. Trigger especially when the user references a spreadsheet file by name or path — even casually (like \"the xlsx in my downloads\") — and wants something done to it or produced from it. Also trigger for cleaning or restructuring messy tabular data files (malformed rows, misplaced headers, junk data) into proper spreadsheets. The deliverable must be a spreadsheet file. Do NOT trigger when the primary deliverable is a Word document, HTML report, standalone Python script, database pipeline, or Google Sheets API integration, even if tabular data is involved.
  source: anthropic
  source_path: https://raw.githubusercontent.com/anthropics/skills/main/skills/xlsx/SKILL.md
  anthropic_compatible: true
  pap_contract_path: null
  anthropic_skill_path: ./anthropic_skills/xlsx/SKILL.md

## Detailed protocol specs

See `.agent/skills/*.md` for local PAP skill contracts. Synced
Anthropic skills are registry entries until they are converted into
local PAP contracts or wired to runtime tool modules.

## Adding new skills

1. Create `agent_runtime/tools/<skill_name>.py` for local runtime skills
2. Implement a `run(params: dict) -> dict` function
3. Add the skill name to `tools:` in `.agent/agent.md`
4. Add a matching protocol document under `.agent/skills/`
5. Include `source`, `anthropic_compatible`, `pap_contract_path`, and
   `anthropic_skill_path` metadata in this registry
