# Episodic Memory / 情境記憶

This directory persists turn-by-turn interaction logs, conversational histories, and tool execution outputs for the agent.

此目錄持久化保存代理（Agent）的對話交互記錄、對話歷史以及工具調用輸出。

---

## 1. Specification / 格式規格
- **File Format**: JSONLines (`.jsonl`) / **檔案格式**：JSONLines (`.jsonl`)
- **Naming Convention**: `session_{session_id}.jsonl` or `{agent_name}_episodic.jsonl` / **命名規範**：`session_{session_id}.jsonl` 或 `{agent_name}_episodic.jsonl`
- **Schema Validation**: Every entry must strictly conform to the `#/$defs/episodic_entry` schema defined in `spec/memory.schema.json` and `.agent/memory/schema.json`. / **Schema 驗證**：每一筆記錄必須嚴格符合 `spec/memory.schema.json` 與 `.agent/memory/schema.json` 中定義的 `#/$defs/episodic_entry`。

## 2. Key Fields / 關鍵欄位
- `id` (string): A unique UUID v4. / 唯一 UUID v4。
- `timestamp` (string): ISO-8601 UTC date-time string. / ISO-8601 UTC 時間字串。
- `role` (string): Enum `["user", "agent"]`. / 角色枚舉。
- `content` (string): The text payload or serialized tool results. / 文本內容或序列化的工具執行結果。
- `tool` (string, optional): The name of the tool executed, if any. / 執行的工具名稱（選填）。
