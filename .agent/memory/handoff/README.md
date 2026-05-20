# Handoff Memory / 交接記憶

This directory stores structured state packets used to transfer context, pending checklists, and snapshots from one agent to another during cross-agent workflows.

此目錄儲存結構化的交接數據包（Handoff Packet），用於在跨代理（Cross-Agent）工作流中轉移上下文、待辦清單以及記憶快照。

---

## 1. Specification / 格式規格
- **File Format**: JSON (`.json`) / **檔案格式**：JSON (`.json`)
- **Naming Convention**: `handoff_{handoff_id}.json` / **命名規範**：`handoff_{handoff_id}.json`
- **Schema Validation**: Every handoff packet must strictly conform to the `#/$defs/handoff_packet` schema defined in `spec/memory.schema.json` and `.agent/memory/schema.json`. / **Schema 驗證**：每個交接包必須嚴格符合 `spec/memory.schema.json` 與 `.agent/memory/schema.json` 中定義的 `#/$defs/handoff_packet`。

## 2. Key Fields / 關鍵欄位
- `task_state` (string): Description of the current task state. / 當前任務狀態的簡短描述。
- `pending_steps` (array of strings): Remaining steps in the task queue. / 剩餘的待辦步驟。
- `context_summary` (string): High-level context summary for the next agent. / 給下一代代理的上下文總結。
- `memory_snapshot` (object): Snapshot of key-value pairs from memory. / 關鍵的記憶狀態快照。
