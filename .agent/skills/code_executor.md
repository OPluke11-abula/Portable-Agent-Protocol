# Skill: code_executor

## 用途

在受控環境中執行程式、腳本或測試。

## 輸入格式

- `runtime`
- `command`
- `working_directory`
- `sandbox_policy`

## 輸出格式

- `stdout`
- `stderr`
- `exit_code`
- `artifacts`

## 失敗處理

- 區分語法、環境、權限錯誤
- 成功修正後，評估是否回寫技能規則
