# Formal Execution Semantics for PAP

The Portable Agent Protocol (PAP) is designed to ensure that AI agents can share, port, and collaboratively mutate state safely. As PAP scales to support multi-agent and concurrent workflows, relying purely on "convention" is insufficient. 

This document defines the formal execution semantics, state machine boundaries, and conflict resolution constraints for the `.agent/` workspace.

## 1. Memory Tier Architecture

To prevent state collisions and clearly define data boundaries, PAP defines four distinct Memory Tiers. Runtimes MUST enforce these boundaries.

*   **Ephemeral (`ephemeral`)**: Short-term context (e.g., current prompt iterations, scratchpads). Destroyed when the agent's immediate task loop ends.
*   **Session (`session`)**: Context tied to a specific user interaction or execution session. Usually maintained in `in_memory` or `redis`.
*   **Persistent (`persistent`)**: Long-term durable memory (e.g., knowledge bases, historical logs). Written to disk (`json`, `sqlite`, or `vector`).
*   **Shared (`shared`)**: Memory specifically designated for inter-agent communication, broadcast, and handoffs. Requires a concurrency-safe backend.

## 2. Concurrency and Conflict Resolution

When multiple agents (or multiple instances of an agent) operate concurrently within the same `.agent/` workspace, write conflicts to `persistent` and `shared` tiers are inevitable.

### 2.1 Pessimistic Locking (Phase 1)
For Phase 1, PAP mandates **Pessimistic Locking** on file-based storage:
1.  **Lock Acquisition**: Before an agent writes to `.agent/memory/`, the runtime must acquire an exclusive lock on the target file/resource.
2.  **Timeout**: Locks must have a strict timeout (default: 5 seconds) to prevent deadlocks.
3.  **Failure**: If a lock cannot be acquired, the runtime must reject the agent's write operation and prompt the agent to retry or abort.

### 2.2 Operational Transformation & CRDTs (Future Roadmap)
To support true real-time, multi-agent collaborative memory manipulation, future versions of PAP will transition to CRDTs (Conflict-free Replicated Data Types) for all `shared` memory objects. 

## 3. Self-Evolution and Schema Constraints

The README describes "self-evolving project workflows." If an agent has the permission to modify `.agent/skills/` (e.g., updating its own tools), it introduces a critical risk: an agent could silently break a skill contract that other agents rely on.

### 3.1 Strict Forward Compatibility
If `schema_evolution.strict_forward_compatibility` is enabled (default), any modification to the `.agent/skills/` directory MUST adhere to these rules:
*   **No Parameter Deletion**: Existing required parameters cannot be removed.
*   **Type Preservation**: The type of an existing parameter cannot change.
*   **New Parameters**: New parameters MUST be strictly optional or have default values.

Runtimes are responsible for validating skill changes against previous versions (stored in git or local cache) before committing the writeback. An agent attempting a breaking change MUST receive a schema validation error and be forced to reconsider.
