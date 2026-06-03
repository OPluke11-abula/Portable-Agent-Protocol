# Changelog

All notable changes to the Portable Agent Protocol (PAP) reference implementation and specifications will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-05-31

This release marks the initial reference implementation of the Portable Agent Protocol (PAP), providing a standard workspace definition for AI agents alongside a standard Python runtime.

### Added

#### 🏗️ Protocol Specifications & Schemas (`.agent/` & `spec/`)
- **Three-Tier Workspace Layout**: Formalized standard workspace organization:
  1. Layer 1: Executable Manifest (`agent.md`).
  2. Layer 2: Runtime Entry Documents (`skills.md`, `prompts.md`, `memory.md`, `workflows.md`, `routing.md`, `handoff_guide.md`).
  3. Layer 3: Detailed Protocol Directories (`skills/`, `prompts/`, `memory/`, `workflows/`, `knowledge_base/`).
- **Declarative Schemas**: Added Draft-07 JSON schemas in `spec/` to validate:
  - `agent-schema.json`: Manifest constraints and folder mappings.
  - `skill-contract.schema.json`: Input/output contracts for agent capabilities.
  - `memory.schema.json`: Long-term, semantic, episodic, and handoff memory tiers.
  - `workflow.schema.json`: Step-by-step DAG pipelines.
  - `knowledge.schema.json`: Metadata for agent-grounded knowledge files.

#### ⚙️ Reference Runtime (`agent_runtime/`)
- **AgentEngine**: Bootstraps the declarative agent configurations, validates version compatibility, and enforces onboarding compliance constraints.
- **Skill Router**: Dynamically resolves and dispatches tool executions to local Python callables, MCP servers, or proprietary services while enforcing input validation against skill contracts.
- **WorkflowEngine**: Executes Directed Acyclic Graph (DAG) workflows with step-level variable interpolation, execution state tracking, failure writeback, and checkpointing for resuming.
- **Memory Tier Backends**: Implemented persistent and ephemeral memory storage backends:
  - `InMemoryBackend` (ephemeral key-value).
  - `JSONFileBackend` (local file persistence).
  - `SQLiteBackend` (durable locking/relational storage).
  - `VectorDBBackend` (fallback-isolated vector stub).
- **Multi-Account Manager & Auditing**: Added thread-safe, process-locked LLM billing manager (`AccountManager` & `LLMClient`) supporting real-time price auditing, token thresholds, and automatic API provider failover.
- **Cross-Agent Handoff**: Standardized integrity-signed (SHA-256) JSON state handoff packets to safely transfer execution contexts between distinct agents.

#### 🛡️ Security Audit & Sandbox Boundaries
- **Prompt Injection Defense**: Implemented HTML/XML variable escaping inside the prompt composer for system prompts, with selective `SafePromptString` overrides.
- **Memory Key Sandboxing**: Strict validation checks to reject key inputs containing path traversal sequences (`/`, `\\`, `..`), null bytes (`\x00`), or lengths exceeding 256 characters.
- **Skill ID Sanitization**: Validation of routing identifiers using strict format checks (`^[a-zA-Z0-9_-]+$`) to prevent arbitrary file reading and traversal attacks.
- **Granular Skill Permission Model**: Implemented authorization level policy checks (`auto`, `interactive-approval`, `deny`) inside the execution flow to enforce human-in-the-loop approvals.

#### ⚡ Performance Benchmarks & Diagnostic Tooling
- **Static Linter**: Implemented a workspace linter (`cli.py lint`) supporting semantic versioning alignments, DAG dependency verification, and "Brain & Hands" decoupling rules (blocking executable files in the knowledge base and global/mutable states in Python tools).
- **Performance Benchmarking Suite**: Implemented `benchmarks/run_benchmarks.py` and `tests/test_performance.py` measuring loading latencies, memory transaction speed (1000 bulk transactions < 10ms in-memory), and workflow parsing overhead.
- **Dependency Minimization**: Refactored the core library package requirements to depend exclusively on `PyYAML>=6.0` and the Python standard library, relocating `jsonschema` and testing utilities into dev optional dependencies.
