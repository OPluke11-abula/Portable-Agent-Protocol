# Runtime Simulation

本示例展示 `.agent/` 在一次執行中的回寫方式。

## 情境

Agent 執行 `query_db` 時發現舊 schema 名稱已失效。

## 正確處理

1. 讀取 `.agent/agent.md`
2. 讀取 `.agent/skills/query_db.md`
3. 檢查 `.agent/knowledge_base/api_docs.md`
4. 驗證新的 schema 名稱
5. 回寫技能或記憶

## 對應示例

- [examples/snapshot/incident_report.md](C:/Users/luke2/Documents/Codex/2026-05-17/findai-portable-agent-protocol-fpap-python/examples/snapshot/incident_report.md)
- [examples/snapshot/skills_update.md](C:/Users/luke2/Documents/Codex/2026-05-17/findai-portable-agent-protocol-fpap-python/examples/snapshot/skills_update.md)
- [examples/snapshot/memory_update.md](C:/Users/luke2/Documents/Codex/2026-05-17/findai-portable-agent-protocol-fpap-python/examples/snapshot/memory_update.md)
