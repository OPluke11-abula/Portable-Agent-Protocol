# FPAP 使用方式

本專案的建議使用方式是：把整個 `.agent/` 目錄複製到你的專案根目錄。

## 1. 安裝

```text
cp -r .agent /your-project/.agent
```

Windows、macOS、Linux 具體複製方式可依環境調整，但目標都是讓 `.agent/` 位於專案根目錄。

## 2. 啟動咒語

把下面這段話貼給你的 AI：

```text
請先閱讀專案根目錄的 .agent/agent.md。
接著依照其中規則，載入相關的 .agent/core、.agent/skills、.agent/prompts、.agent/memory、.agent/knowledge_base。
你必須把 .agent 視為本專案的 Agent 協作規格來源。
完成任務後，除了交付結果，也要評估是否需要回寫 skills、memory 或 knowledge_base。
未驗證內容不得寫成正式規則。
```

## 3. 讀取順序

建議 AI 每次依序讀取：

1. `.agent/agent.md`
2. 任務相關的 `.agent/core/*.md`
3. 任務相關的 `.agent/skills/*.md`
4. 需要時讀取 `.agent/prompts/*.md`
5. 讀取 `.agent/memory/*.md`
6. 檢索 `.agent/knowledge_base/*`

## 4. 回寫規則

- 新的工具使用流程：寫到 `.agent/skills/`
- 新的錯誤修復策略：先看是否該補到 `.agent/prompts/` 或 `.agent/skills/`
- 當前會話狀態：寫到 `.agent/memory/short_term_cache`
- 穩定長期知識：寫到 `.agent/memory/vector_db` 或 `.agent/knowledge_base/`
- 跨任務高槓桿規則：才更新 `.agent/agent.md`

## 5. 演進路徑

如果之後要從模板升級為可執行 Agent，可逐步增加：

- `.agent/core/*.py`
- `.agent/skills/*.py`
- `.agent/logs/`
- `.agent/runtime/`

但初版先不要混進太多執行層，否則協定與實作會一起漂移。
