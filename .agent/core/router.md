# Router Spec

`router` 是狀態機與決策路由層。

## 責任

- 判斷當前任務屬於哪種類型
- 決定要讀哪些技能
- 決定何時查知識、何時執行工具、何時進入驗證
- 遇到失敗時決定重試、降級或請求人類介入

## 典型狀態

- `intake`
- `context_loading`
- `planning`
- `execution`
- `verification`
- `writeback`
- `final_response`

## 路由原則

- 優先最小可行步驟
- 失敗後先查 `.agent/prompts/error_handling.md`
- 非必要不升級為人工阻塞
