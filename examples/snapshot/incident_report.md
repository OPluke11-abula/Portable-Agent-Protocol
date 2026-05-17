# Incident Report Example

舊版文件中的 schema alias 已過時，導致查詢流程失敗。

## 影響

- 新進 Agent 會重複踩坑
- 查詢流程可靠性下降

## 修正

- 更新 `.agent/skills/query_db.md`
- 將 alias 映射規則寫入長期記憶
