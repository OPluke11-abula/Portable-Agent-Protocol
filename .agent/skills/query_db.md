# Skill: query_db

## 用途

提供結構化資料查詢能力。

## 輸入格式

- `connection_target`
- `query_intent`
- `filters`
- `safety_constraints`

## 輸出格式

- `rows`
- `schema_used`
- `query_summary`
- `risk_notes`

## 安全原則

- 預設只讀
- 執行前先確認 schema
- 高風險查詢需明確授權
