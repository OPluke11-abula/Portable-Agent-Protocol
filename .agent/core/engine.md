# Core Engine Spec

`engine` 負責解讀 `.agent/agent.md`，組裝本輪任務所需的上下文，並驅動與模型的互動。

## 責任

- 載入 Agent Manifest
- 選取相關 skills、prompts、memory、knowledge
- 組合執行上下文
- 產生工具呼叫意圖

## 輸入

- 使用者任務
- `.agent/agent.md`
- 相關 `.agent/skills/*.md`
- 相關 `.agent/prompts/*.md`
- `.agent/memory/*`
- `.agent/knowledge_base/*`

## 輸出

- 本輪上下文包
- 對 router 的下一步建議
- 工具或子流程選擇建議
