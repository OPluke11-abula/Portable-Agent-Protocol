# Memory Management Guide: State Persistence in PAP

A persistent and structured memory subsystem is vital for AI agents to maintain continuity across runtime restarts, coordinate multiple sub-tasks, and hand off tasks securely to other agents.

The **Portable Agent Protocol (PAP)** formalizes memory into three standard-compliant structures:
1. **Semantic Memory**: A key-value persistent fact and variable store.
2. **Episodic Memory**: A stream of historic agent observations and actions.
3. **Handoff Memory**: Encrypted or verified state packets transferred between agents.

---

## 1. Defining Memory Settings (`.agent/memory.md`)

Persistence is configured in `.agent/memory.md`. This file specifies which storage backend to mount and the path where memory files reside.

```yaml
---
schema_version: "1.0.0"
backend: "local"
path: ".agent/memory/"
encryption:
  enabled: false
---
# Memory Configuration
```

Currently, the PAP reference implementation supports the `local` backend, which stores state in standard formats inside the designated `path` directory.

---

## 2. The Three Pillars of PAP Memory

### 2.1. Semantic Memory (Persistent Facts & Variables)
Semantic memory stores static facts, configuration variables, and intermediate results as a serialized JSON key-value object in `<path>/memory.json`.

#### Structure Example:
```json
{
  "active_database": "production_v2",
  "migration_completed": true,
  "system_errors_encountered": 0
}
```

### 2.2. Episodic Memory (Action-Observation Streams)
Episodic memory preserves the chronological log of agent interactions. Each transaction is appended as a JSON object inside a JSON Lines (`.jsonl`) file, ensuring fast, O(1) writes.

#### Structure Example (`.agent/memory/memory_episodic_sample.jsonl`):
```json
{"timestamp": "2026-05-21T00:00:01Z", "role": "system", "event": "boot", "details": "AgentEngine initialised."}
{"timestamp": "2026-05-21T00:00:05Z", "role": "agent", "event": "skill_call", "skill_id": "list_dir", "params": {"path": "."}}
{"timestamp": "2026-05-21T00:00:06Z", "role": "environment", "event": "skill_result", "skill_id": "list_dir", "status": "success"}
```

### 2.3. Handoff Memory (Multi-Agent Transfers)
Handoff memory maps out temporary snapshot packets containing active state summaries, list of pending DAG steps, and extracted memory variables. Packets are stored under `<path>/handoff/<handoff_id>.json` and protected by SHA-256 integrity checksums.

#### Structure Example:
```json
{
  "handoff_id": "migration-v1",
  "protocol_version": "1.0.0",
  "timestamp": "2026-05-21T00:45:00Z",
  "source_agent": "AgentA",
  "task_state": "Database migrated to staging. Primary key indices missing.",
  "pending_steps": ["create_indices", "run_smoke_tests"],
  "context_summary": "Staging DB connection parameters: HOST=127.0.0.1 PORT=5432.",
  "memory_snapshot": {
    "active_database": "production_v2"
  },
  "checksum": "3d37a3cb0ff9e0dd2a8fb16461396c11f3922aded94a9c723a43b3b036fb16d5"
}
```

---

## 3. Working with the Memory API in Python

The reference Python implementation exposes memory management through the `AgentEngine.memory` object.

### Basic Memory Operations

```python
from agent_runtime.engine import AgentEngine

# Initialize the engine
engine = AgentEngine(".agent/agent.md")

# 1. Write values to semantic memory
engine.memory.write("target_environment", "production")
engine.memory.write("max_retry_attempts", 3)

# 2. Read values from semantic memory
env = engine.memory.read("target_environment")
retries = engine.memory.read("max_retry_attempts", default=1)
print(f"Active Env: {env}, Max Retries: {retries}")

# 3. List or query keys in semantic memory
all_keys = engine.memory.keys()
print(f"Stored keys in workspace: {all_keys}")
```

### Handoff Management

```python
# 1. Export state for another agent
handoff_id = "task-sync-2026"
engine.export_handoff(
    task_state="Completed API route scaffold.",
    pending_steps=["Write tests", "Format codebase"],
    context_summary="Route handlers defined in backend/routes.py",
    memory_keys=["target_environment"],
    handoff_id=handoff_id
)
print("Handoff packet successfully written and checksummed!")

# 2. Import state in another agent
# Under the hood, this validates the SHA-256 checksum and restores 'target_environment' in semantic memory.
imported_state = engine.import_handoff(handoff_id)
print(f"Restored Task State: {imported_state['task_state']}")
```

---

## 4. Best Practices for Memory Design

To build robust agents, keep these memory paradigms in mind:

* **Isolate Workspace Memory**: Avoid hardcoding absolute paths. Set the memory path in `agent.md` dynamically or use relative references (`.agent/memory/`) to ensure the agent remains portable across environments.
* **JSON Serializability**: Only store basic JSON-compatible data types (strings, numbers, booleans, lists, and dicts) in semantic memory. Complex Python objects (like file handles or socket connections) cannot be serialized.
* **Write Small, Atomic Keys**: Prefer saving granular parameters (e.g. `current_index: 12`) over storing massive, nested data tables in semantic memory. Use the local workspace filesystem or a database database for massive payloads, keeping memory agile.
* **Use Handoff Checksums**: Always allow the protocol to verify checksums during multi-agent transfers. This safeguards the destination agent against malicious state injections or transmission corruption.

---

## 5. Evidence Memory Proposal

PAP also defines an opt-in evidence memory proposal in
`spec/evidence-memory.schema.json`. This proposal is for workspaces that need
traceable summarized memory without changing existing semantic, episodic, or
handoff backends.

The proposal defines these layers:

| Layer | Field | Purpose |
| --- | --- | --- |
| L0 | `l0_raw_evidence_refs` | Raw files, command outputs, URLs, logs, artifacts, or manual observations. |
| L1 | `l1_atoms` | Atomic summarized claims. Each atom requires `trace_refs`. |
| L2 | `l2_scenarios` | Scenario summaries composed from atoms or evidence. Each scenario requires `trace_refs`. |
| L3 | `l3_profile` | Persona/profile claims. Each profile claim requires `trace_refs`. |
| Canvas | `mermaid_canvases` | Mermaid canvas references with `node_id`, `result_ref`, and `trace_refs`. |

Every summarized memory claim must trace back to raw evidence, a canonical
artifact, or an already-traced lower-level memory record. The schema is
documentation and validation surface only. It does not install automatic capture
hooks, start memory daemons, patch OpenClaw, or configure remote memory
gateways.
