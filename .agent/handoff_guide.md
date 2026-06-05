# Multi-Generational Thread Handoff Protocol (Thread-Hopping)

To prevent LLM context drift, attention decay, and token budget explosion during long-running sessions, this workspace enforces a strict **Thread-Hopping** protocol. Agents are instructed to actively transition tasks across clean thread boundaries when context size becomes bloated.

---

## 🔄 The Thread-Hopping Pipeline

```
Long-Turn Session (Drift & Bloat) ➔ Export Handoff Packet ➔ Spawn Clean Thread ➔ Ingest Packet ➔ Warm Start
```

---

## 🧭 Clean Onboarding Sequence

Every newly spawned Agent must read files in this exact order to reconstruct 100% state alignment under 0.1 seconds:

1. **`agent.md` (Persona & Config)**: Load the identity, Hard Rules, and capability settings.
2. **`skills.md` (Active Skills)**: Understand active tool contracts, schemas, and resolution paths.
3. **`agent_tasks.md` (Task Backlog & Logs)**: Scan the active checklist, current progress, and historical execution records.
4. **`handoff_guide.md` (Handoff SOP - This File)**: Retrieve specific parameters, checkpoints, and transition protocols.

---

## 📦 Handoff Packet Schema (`.agent/memory/handoff/<id>.json`)

The handoff packet is exported dynamically using the engine's built-in handoff routines. The JSON payload must conform to the following schema structure:

```json
{
  "task_state": "String describing the exact current status of the task.",
  "pending_steps": [
    "List of next immediate actionable items/steps."
  ],
  "context_summary": "English summary of changes made, systems touched, and architectural decisions.",
  "memory_snapshot": {
    "key1": "Value1",
    "key2": "Value2"
  },
  "checksum": "SHA-256 integrity signature generated over the canonical serialized JSON payload."
}
```

### Integrity Verification:
Upon importing, the receiving agent's runtime validates the checksum to prevent corruption, tampering, or partial transfer failures:
$$\text{SHA-256}(\text{Canonical JSON without checksum}) \stackrel{?}{=} \text{checksum}$$

---

## 🎬 Handoff Trigger SOP

1. **Turn-Based Detection**: Keep track of execution turn count. Spawn a new clean agent instance and perform thread-hopping every **5 to 15 turns** to maintain active context reasoning quality.
2. **Task Registry Compaction**: Every **5 to 15 turns**, consolidate the completed tasks in `agent_tasks.md`, merging individual detailed items under completed phases into dense milestone summaries to optimize token usage.
3. **Information Pruning**: Clean up local redundant caches, terminal outputs, and temporary variables. Keep the workspace clean and prune untracked debug outputs.
4. **State Export**: Run `engine.export_handoff(...)` to write the `.json` state packet to the handoff registry.
5. **English Handoff Prompt**: Formulate a complete, comprehensive **English Handoff Prompt** for the incoming agent, transferring exact task status, next immediate actions, and structural context.
