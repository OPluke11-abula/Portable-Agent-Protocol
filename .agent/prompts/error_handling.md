---
id: error_handling
version: 1.0.0
usage: Guidelines for error handling, failure recovery and escalation
variables: []
---
當工具、技能或依賴失敗時，請依序處理：

1. 確認是否可重現
2. 判斷屬於輸入、環境、權限或設計缺口
3. 檢查 `.agent/knowledge_base/` 是否已有答案
4. 嘗試最小可驗證修正
5. 成功後決定是否回寫 `.agent/`

回報時必須包含：

- 失敗點
- 已檢查內容
- 下一步建議
