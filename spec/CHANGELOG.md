# CHANGELOG

All notable changes to the Portable Agent Protocol (PAP) specifications and reference runtimes will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Opt-in workflow governance manifest schema for stages, directors, canonical artifacts, allowed actions, and approval policy.
- Workflow checkpoint schema for artifact hashes, evidence references, verifier metadata, unresolved risks, and checkpoint status.
- Read-only workspace lint validation for opt-in workflow governance manifests and checkpoints.
- Opt-in evidence memory schema proposal for L0 raw evidence refs, L1 atoms, L2 scenarios, L3 persona/profile claims, and Mermaid canvas references.
- Report-only structured review and security findings schema with high/critical exploit path requirements.
- LAS interop validation plan for ConductorPlan, LongTermMemoryStore, UnifiedPolicyGate, and AuditLedger compatibility.

---

## [0.1.0] - 2026-05-20

### Added
- **Core Engine**: Implemented `AgentEngine` bootstrap loading `.agent/agent.md` configs and layout specifications.
- **Protocol Schema Validation**: Formulated standard JSON Schemas under `spec/` for manifests, skills, workflows, knowledge base, and memory.
- **Router**: Created standard tools registry (`Router.list_skills`, `Router.describe_skill`) and automated inputs validation.
- **Workflow Engine**: Added automated DAG multi-step workflow executor (`WorkflowEngine`) with step resume capabilities.
- **Knowledge Base**: Implemented read-only markdown-based knowledge retrieval with front-matter indexing.
- **Prompt Registry**: Created `PromptComposer` for templating registry prompts and added strict injection scanning.
- **Cross-Agent State Handoff**: Formulated inter-agent state serialization with signature integrity using SHA-256 canonical hashing.
- **Reference CLI**: Designed complete CLI tools supporting validation, memory read/write, workflow runs, sync, hub clone/pack, and handoffs.
