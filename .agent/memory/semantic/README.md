# Semantic Memory / 語意記憶

This directory persists long-term structured knowledge, state, concepts, and persistent variables that survive across sessions.

此目錄持久化保存長期結構化知識、狀態、概念以及跨 Session 存活的持久化變數。

---

## 1. Specification / 格式規格
- **File Format**: JSON (`.json`) / **檔案格式**：JSON (`.json`)
- **Naming Convention**: `{concept_key}.json` or general key-value collection / **命名規範**：`{concept_key}.json` 或通用的鍵值對集合
- **Schema Validation**: Every entry must strictly conform to the `#/$defs/semantic_record` schema defined in `spec/memory.schema.json` and `.agent/memory/schema.json`. / **Schema 驗證**：每一筆記錄必須嚴格符合 `spec/memory.schema.json` 與 `.agent/memory/schema.json` 中定義的 `#/$defs/semantic_record`。

## 2. Key Fields / 關鍵欄位
- `key` (string): A unique identifier matching `^[a-zA-Z0-9_-]+$`. / 匹配 `^[a-zA-Z0-9_-]+$` 的唯一識別碼。
- `value` (any): The concept payload (primitive or complex). / 概念資料主體（可為基本型別或複雜物件）。
- `metadata` (object, optional):
  - `created_at` (string, ISO-8601): Creation time. / 建立時間。
  - `updated_at` (string, ISO-8601): Update time. / 更新時間。
  - `tags` (array of strings): Category/index tags. / 分類/索引標籤。
