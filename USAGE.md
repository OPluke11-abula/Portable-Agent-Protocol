# FPAP 使用方式

建議的使用方式是把整個 `.agent/` 目錄複製到你的專案根目錄，保留其分層結構。

## 1. 安裝

```text
cp -r .agent /your-project/.agent
```

Windows、macOS、Linux 的實際複製指令可以依環境調整，但目標都一樣：
讓 `.agent/` 位於專案根目錄。

## 2. 啟動咒語

把下面這段話貼給你的 AI：

```text
請先閱讀專案根目錄的 .agent/agent.md。
接著閱讀 .agent/README.md，確認這個專案的 .agent/ 架構是「manifest + runtime entry documents + detailed directories」三層模型。
再依任務需要，優先讀取相關的 .agent/skills.md、.agent/prompts.md、.agent/memory.md、.agent/workflows.md。
最後再深入讀取對應子目錄中的 .agent/core、.agent/skills、.agent/prompts、.agent/memory、.agent/workflows、.agent/knowledge_base。
你必須把 .agent 視為本專案的 Agent 協作規格來源。
完成任務後，除了交付結果，也要評估是否需要回寫 skills、memory、workflow note 或 knowledge_base。
未驗證內容不得寫成正式規則。
```

## 3. 讀取順序

建議 AI 每次依序讀取：

1. `.agent/agent.md`
2. `.agent/README.md`
3. 任務相關的頂層入口檔：
   `.agent/skills.md`、`.agent/prompts.md`、`.agent/memory.md`、`.agent/workflows.md`
4. 任務相關的詳細文件：
   `.agent/core/*.md`、`.agent/skills/*.md`、`.agent/prompts/*.md`、`.agent/memory/*.md`、`.agent/workflows/*.md`
5. `.agent/knowledge_base/*`

## 4. 回寫規則

- 新的 runtime capability：同步更新 `.agent/agent.md`、`.agent/skills.md`、對應 runtime 模組與 `.agent/skills/*.md`
- 新的 prompt policy：更新 `.agent/prompts/`
- 新的 workflow：更新 `.agent/workflows.md`，並補一份 `.agent/workflows/*.md` note
- 會話期狀態與短期記憶慣例：更新 `.agent/memory/`
- 穩定長期知識：更新 `.agent/knowledge_base/`
- 只有跨任務的高槓桿規則才更新 `.agent/agent.md`

## 5. 演進路徑

如果之後要從模板升級為更完整的可執行 Agent，可以逐步增加：

- `.agent/core/*.py`
- `.agent/skills/*.py`
- `.agent/logs/`
- `.agent/runtime/`

但初版先不要把太多執行層混進協定層，否則規格與實作會一起漂移。
