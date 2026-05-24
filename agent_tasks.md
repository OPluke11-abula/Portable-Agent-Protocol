# PAP Agent Task Queue
>
> Protocol: portable-agent-protocol v0.1.0  
> Format: PAP Task Contract v1  
> Status legend: `[ ]` pending · `[~]` in-progress · `[x]` done · `[!]` blocked

---

## PHASE 0 — Foundation / 基礎建設

### 0-00 代理身份與引導配置 (.AGENT)

```
priority : CRITICAL
effort   : S
depends  : —
```

- [x] 在根目錄建立 `.AGENT.md` 引導設定檔，定義 Systems Programmer 代理身份與 5 大工作結束規則
- [x] 在根目錄建立 `.cursorrules`，自動導引外部 AI 編輯器載入 `.AGENT.md` 與 `.agent/agent.md`
- [x] 更新 `.agent/agent.md` YAML 聲明，配置 `programmer-agent` 身份與 `tasks` 進入點
- [x] 執行驗證與單元測試，確保完全符合 `spec/agent-schema.json`

---

### 0-01 Schema 正式化

```
priority : CRITICAL
effort   : M
depends  : —
```

- [x] 建立 `spec/` 目錄
- [x] 撰寫 `spec/agent-schema.json`，定義 `.agent/agent.md` YAML front matter 的完整 JSON Schema
- [x] 撰寫 `spec/skill-contract.schema.json`，定義 capability contract 的欄位規格
- [x] 撰寫 `spec/memory.schema.json`，定義 episodic / semantic memory 的資料格式
- [x] 撰寫 `spec/workflow.schema.json`，定義 workflow 步驟結構
- [x] 在 `README.md` 加入 `spec/` 的說明段落
- [x] 驗證現有 `.agent/` 下的所有 .md 都符合新 schema

---

### 0-02 Memory 格式落地

```
priority : CRITICAL
effort   : M
depends  : 0-01
```

- [x] 建立 `.agent/memory/episodic/` 目錄，加入 `README.md` 說明格式
- [x] 建立 `.agent/memory/semantic/` 目錄，加入 `README.md`
- [x] 建立 `.agent/memory/handoff/` 目錄，用於跨 agent 交接
- [x] 撰寫 `.agent/memory/schema.json`，定義所有欄位與型別
- [x] 新增範例檔 `examples/memory_episodic_sample.jsonl`
- [x] 新增範例檔 `examples/memory_semantic_sample.json`
- [x] 新增範例檔 `examples/memory_handoff_sample.json`
- [x] 在 `agent_runtime/` 實作 `MemoryBackend` 類別，支援 read / write / query
- [x] 補充對應測試 `tests/test_memory_backend.py`

---

### 0-03 Skill Contract 標準化

```
priority : HIGH
effort   : S
depends  : 0-01
```

- [x] 為現有每個 tool 補齊 `.agent/skills/<tool>.md`（若缺漏）
- [x] 確認每個 skill contract 包含欄位：`id`, `description`, `inputs`, `outputs`, `safety_notes`, `version`
- [x] 移除任何 skill contract 中對特定 AI 廠商的參照
- [x] 在 `.agent/skills.md` registry 加入 `schema_version` 欄位
- [x] 補充測試 `tests/test_skill_contracts.py`，驗證每個 skill 都符合 schema

---

### 0-04 Router 強化

```
priority : HIGH
effort   : M
depends  : 0-03
```

- [x] `agent_runtime/router.py` 加入 schema 驗證：呼叫前檢查 inputs 是否符合 skill contract
- [x] 加入 `Router.list_skills()` 方法，回傳結構化的 skill 清單
- [x] 加入 `Router.describe_skill(skill_id)` 方法，回傳單一 skill 的 contract 內容
- [x] 加入 `Router.validate_call(skill_id, params)` 方法，呼叫前乾跑驗證
- [x] 加入 routing 失敗時的明確錯誤訊息（包含 skill_id、缺少欄位名稱）
- [x] 補充測試 `tests/test_router_validation.py`

---

### 0-05 CLI 完整化

```
priority : MEDIUM
effort   : S
depends  : 0-04
```

- [x] `cli.py` 加入 `--list-skills` 指令，印出所有可用 skill 清單
- [x] `cli.py` 加入 `--describe-skill <id>` 指令，印出 skill contract 詳情
- [x] `cli.py` 加入 `--validate` 指令，檢查整個 `.agent/` 結構是否合法
- [x] `cli.py` 加入 `--memory-read <key>` 指令
- [x] `cli.py` 加入 `--memory-write <key> <value>` 指令
- [x] `cli.py` 加入 `--run-workflow <id>` 指令
- [x] 更新 `USAGE.md` 反映新 CLI 選項

---

### 0-06 Open Source Skills 引入與匿名化

```
priority : HIGH
effort   : M
depends  : 0-03
```

- [x] 從 `https://github.com/anthropics/skills` 拷貝有用的開源技能（如文件處理、網頁搜尋等）
- [x] 將這些技能合約手動存放至 `.agent/skills/`
- [x] 移除這些合約與程式碼中的 "Anthropic" 相關字眼與商標
- [x] 修改內部邏輯，使其完全相容於我們純本地端的 Python 執行器 (Router)
- [x] 確認這些被「挪用」的技能不再發送任何外部 API 請求，或已將其轉換為通用的 LLM 呼叫

---

### 0-07 Onboarding 順序性與強制性校驗 (Strict Onboarding Verifier)

```
priority : HIGH
status   : [x] done
effort   : S
depends  : 0-00
```

- [x] 在 `AgentEngine` 初始化階段實作 Onboarding 順序校驗機制
- [x] 追蹤 episodic memory，強制檢查 `agent.md ➔ skills.md ➔ agent_tasks.md ➔ handoff_guide.md` 讀取鏈
- [x] 未完成 onboarding 前，限制其他 tool/skill 調用，確保認知對齊

---

### 0-08 實作 tool_manifest.py 整合與全局技能屏蔽機制

```
priority : MEDIUM
effort   : S
depends  : 0-03
```

- [x] 撰寫 `agent_runtime/tool_manifest.py` 定義 Local/Global 技能清單
- [x] 在 `cli.py lint` 與 `pytest` 執行本地一致性校驗時自動屏蔽/忽略全局技能（如 `pdf`, `xlsx`）
- [x] 確保本地專案部署驗證 100% 通過，不因缺乏全局依賴而失敗

---

## PHASE 1 — Protocol Completeness / 協定完整性

### 1-01 Workflow 引擎實作

```
priority : HIGH
effort   : L
depends  : 0-04
```

- [x] 設計 workflow 狀態機格式（states: pending / running / success / failed / skipped）
- [x] 在 `agent_runtime/` 新增 `workflow_engine.py`
- [x] 實作 `WorkflowEngine.load(workflow_id)` —— 從 `.agent/workflows/<id>.md` 載入定義
- [x] 實作 `WorkflowEngine.run(workflow_id, payload)` —— 依序執行步驟
- [x] 實作 `WorkflowEngine.resume(workflow_id, step_id)` —— 從中斷點繼續
- [x] 實作失敗步驟自動寫入 memory（不可靜默失敗）
- [x] 補充測試 `tests/test_workflow_engine.py`（含失敗路徑測試）
- [x] 新增範例 `examples/workflow_run_sample.py`

---

### 1-02 Knowledge Base 索引

```
priority : MEDIUM
effort   : M
depends  : 0-01
```

- [x] 建立 `.agent/knowledge_base/index.json`，記錄所有知識條目的 id、標題、路徑、標籤
- [x] 定義知識條目的 front matter 格式（`id`, `title`, `tags`, `created`, `updated`）
- [x] 為現有 `knowledge_base/` 下的所有文件補充 front matter
- [x] 在 `agent_runtime/` 新增 `knowledge.py`，實作 `KnowledgeBase.query(keyword)` 方法
- [x] 實作 `KnowledgeBase.get(id)` 方法，回傳單一知識條目
- [x] 補充測試 `tests/test_knowledge_base.py`
- [x] 知識庫唯讀保護：任何寫入操作需走 T-04 Protocol Evolution 流程

---

### 1-03 Prompt Registry 可執行化

```
priority : MEDIUM
effort   : M
depends  : 0-01
```

- [x] 定義 prompt snippet 的結構格式（`id`, `template`, `variables`, `usage`, `version`）
- [x] 將 `.agent/prompts/` 下的文件轉換為符合新格式的 prompt contract
- [x] 在 `agent_runtime/` 新增 `prompt_composer.py`，實作 `PromptComposer.build(id, vars)` 方法
- [x] 加入 prompt injection 安全驗證（拒絕未經驗證的外部字串進入 system prompt）
- [x] 補充測試 `tests/test_prompt_composer.py`（含 injection 防護測試）
- [x] 新增範例 `examples/prompt_composition_sample.py`

---

### 1-04 Cross-Agent Handoff 機制

```
priority : HIGH
effort   : M
depends  : 0-02, 1-01
```

- [x] 設計 handoff packet 格式（task_state, pending_steps, context_summary, memory_snapshot）
- [x] 實作 `AgentEngine.export_handoff()` —— 產生 handoff packet 並寫入 `.agent/memory/handoff/`
- [x] 實作 `AgentEngine.import_handoff(handoff_id)` —— 讀取並還原 handoff 狀態
- [x] 加入 handoff packet 的完整性驗證（checksum 或 hash）
- [x] 補充測試 `tests/test_handoff.py`
- [x] 新增範例 `examples/handoff_export_import.py`
- [x] 在 `USAGE.md` 補充跨 agent 交接的使用說明

---

### 1-05 Protocol Version Management

```
priority : MEDIUM
effort   : S
depends  : 0-01
```

- [x] 在 `spec/` 建立 `CHANGELOG.md`，從 v0.1.0 開始記錄
- [x] 定義版本號規則（major.minor.patch，破壞性變更需 major 遞增）
- [x] 在 `agent_runtime/engine.py` 加入版本相容性檢查（runtime version vs. manifest version）
- [x] 版本不相容時輸出明確警告，不直接報錯崩潰
- [x] 建立 `spec/migration/` 目錄，放置版本遷移指南
- [x] 補充測試 `tests/test_version_compat.py`

---

### 1-06 跨層級技能尋址與覆蓋機制 (Layered Skill Pipeline)

```
priority : HIGH
effort   : M
depends  : 0-03
```

- [x] 在 `Router` 實作本地 `.agent/skills/` 與全局 `~/.gemini/antigravity/skills/` 的雙層尋址鏈
- [x] 支援專案本地技能合約直接覆蓋同名全域技能
- [x] 補充層級覆蓋與 fallback 機制的單元測試

---

### 1-07 命令行工作流斷點續傳支援 (Checkpoint-based Resume in CLI)

```
priority : HIGH
effort   : S
depends  : 1-01
```

- [x] 在 `cli.py` 新增 `--resume-workflow <session_id> [--step <step_id>]` 參數
- [x] 實作讀取 `runs/<session_id>.json` 狀態並自動恢復工作流執行
- [x] 補充 CLI 斷點恢復與重試機制的整合測試

---

### 1-08 自動化 Token 溢出偵測與交接觸發器 (Auto Thread-Hopping Trigger)

```
priority : HIGH
effort   : M
depends  : 1-04
```

- [x] 在 `AgentEngine` 核心實作轉數（Turn-count）與 Context 長度計量追蹤
- [x] 當累計 Token 超過 32k 或轉數超限時，自動攔截並執行 `export_handoff()`
- [x] 拋出 `HandoffRequired` 例外，並以特定 Exit Code 退出，通知 Host 重啟乾淨線程

---

### 1-09 工作流實體檔案 Checkpoint 匯出器 (Workflow File Checkpoint Exporter)

```
priority : MEDIUM
effort   : S
depends  : 1-01
```

- [x] 在 `WorkflowEngine._save_session` 中，自動在本地產生 `runs/<session_id>.json` 檔案
- [x] 提供視覺化或外部系統直讀工作流 DAG 步驟狀態的管道
- [x] 確保非破壞性恢復（--resume）能安全解析 runs 目錄下的實體 JSON 狀態

---

## PHASE 2 — Developer Experience / 開發者體驗

### 2-01 Init 指令

```
priority : HIGH
effort   : M
depends  : 0-05, 1-05
```

- [x] `cli.py` 加入 `init` 子指令：在任意專案目錄建立完整的 `.agent/` 骨架
- [x] init 流程詢問：project name、agent name、啟用的 skill 清單
- [x] init 自動產生：`agent.md`、`skills.md`、`prompts.md`、`memory.md`、`workflows.md`、`knowledge_base/`
- [x] init 產生的所有檔案都帶有正確的 YAML front matter 與 schema 版本
- [x] 加入 `--dry-run` 選項，只顯示會產生的檔案，不實際寫入
- [x] 補充測試 `tests/test_cli_init.py`
- [x] 更新 `USAGE.md` 和 `README.md`

---

### 2-02 Lint 指令

```
priority : MEDIUM
effort   : M
depends  : 0-01, 2-01
```

- [x] `cli.py` 加入 `lint` 子指令：檢查 `.agent/` 所有檔案的格式合規性
- [x] 檢查項目：schema 欄位完整性、版本號格式、skill contract 與 registry 一致性、workflow 步驟引用合法性
- [x] 輸出格式：每個問題顯示 severity（error / warning / info）、檔案路徑、行號（若適用）、修復建議
- [x] 加入 `--fix` 選項，自動修復可自動化處理的問題
- [x] 補充測試 `tests/test_cli_lint.py`

---

### 2-03 多語言 Runtime 規格文件

```
priority : MEDIUM
effort   : L
depends  : 0-01
```

- [x] 在 `spec/` 撰寫 `runtime-interface.md`：定義 any 語言的 runtime 必須實作的介面
- [x] 必要介面清單：`load_manifest()`, `list_skills()`, `call_skill()`, `read_memory()`, `write_memory()`, `run_workflow()`
- [x] 為每個介面定義輸入/輸出的 JSON 格式
- [x] 撰寫 JavaScript/TypeScript reference implementation 的 stub（`spec/stubs/ts/`）
- [x] 撰寫 Go reference stub（`spec/stubs/go/`）
- [x] 確保 Python runtime 完全符合此規格文件

---

### 2-04 範例庫擴充

```
priority : LOW
effort   : M
depends  : 1-01, 1-02, 1-03
```

- [x] `examples/` 新增：`00_quickstart.py` —— 5 分鐘上手範例
- [x] `examples/` 新增：`01_skill_call.py` —— 完整的 skill 呼叫流程
- [x] `examples/` 新增：`02_memory_session.py` —— session 記憶讀寫
- [x] `examples/` 新增：`03_workflow_run.py` —— 執行一個多步驟 workflow
- [x] `examples/` 新增：`04_knowledge_query.py` —— 查詢知識庫
- [x] `examples/` 新增：`05_multi_agent.py` —— 模擬兩個 agent 交接任務
- [x] `examples/` 新增：`06_prompt_compose.py` —— 組裝 prompt 並注入變數
- [x] 每個範例都要能獨立執行，有完整的 inline 說明註解

---

### 2-05 文件網站結構

```
priority : LOW
effort   : L
depends  : 2-03, 2-04
```

- [x] 建立 `docs/` 目錄
- [x] `docs/getting-started.md` —— 安裝、init、第一個 skill call
- [x] `docs/protocol-spec.md` —— 完整協定規格（從 spec/ 整合）
- [x] `docs/skill-authoring.md` —— 如何撰寫 capability contract
- [x] `docs/memory-guide.md` —— memory 策略與最佳實踐
- [x] `docs/workflow-guide.md` —— workflow 設計模式
- [x] `docs/multi-agent.md` —— 多 agent 協作與 handoff 指南
- [x] `docs/migration/` —— 各版本遷移指南

---

### 2-06 腦手分離合規性靜態檢查 (Decoupling Static Linter)

```
priority : HIGH
status   : [x] done
effort   : M
depends  : 2-02
```

- [x] 在 `cli.py lint` 實作腦手分離合規性靜態掃描
- [x] 自動驗證 `.agent/knowledge_base/` 僅包含宣告式架構/SOP，無 hardcoded 代碼或工具實現
- [x] 自動驗證 `agent_runtime/tools/` 與 `skills/` 為無狀態，無硬編碼的業務領域邏輯

---

## PHASE 3 — Quality & Security / 品質與安全

### 3-01 測試覆蓋率提升

```
priority : HIGH
status   : [x] done
effort   : M
depends  : PHASE 0, PHASE 1
```

- [x] 設定測試覆蓋率目標：核心 runtime 80% 以上
- [x] 補充 `tests/test_engine.py`：涵蓋邊界條件（缺少欄位、格式錯誤、版本不符）
- [x] 補充 `tests/test_router.py`：涵蓋不存在的 skill、參數型別錯誤
- [x] 補充 `tests/test_memory.py`：涵蓋 scope 隔離、大量資料、concurrent write
- [x] 加入整合測試 `tests/integration/`：模擬完整的 session 流程
- [x] 在 `pyproject.toml` 加入覆蓋率設定（pytest-cov）
- [x] CI 設定：覆蓋率低於門檻時 fail

---

### 3-02 安全審查

```
priority : HIGH
effort   : M
depends  : 1-03
```

- [x] 審查所有可接受外部輸入的路徑，加入輸入驗證
- [x] Prompt injection 防護：確認 `prompt_composer.py` 的 variable 注入有 escaping
- [x] Memory key 注入防護：驗證 key 格式，拒絕含有路徑分隔符號的 key
- [x] Skill call 權限模型：定義哪些 skill 需要明確的使用者授權才能執行
- [x] 撰寫 `spec/security.md`，記錄威脅模型與防護措施
- [x] 補充 `tests/test_security.py`，包含 injection 攻擊的測試案例

---

### 3-03 效能基準測試

```
priority : LOW
effort   : S
depends  : 3-01
```

- [ ] 建立 `benchmarks/` 目錄
- [ ] 基準測試：manifest 載入時間（目標 < 50ms）
- [ ] 基準測試：skill registry 查詢時間（目標 < 10ms）
- [ ] 基準測試：memory 讀寫時間（目標 < 100ms for 1000 entries）
- [ ] 基準測試：workflow 步驟 routing 時間
- [ ] 建立效能回歸測試，合併前自動執行

---

### 3-04 Dependency 最小化

```
priority : MEDIUM
effort   : S
depends  : PHASE 1
```

- [ ] 審查 `pyproject.toml` 的所有依賴，移除非必要套件
- [ ] 區分 runtime 必要依賴 vs. dev 依賴
- [ ] 確認 core runtime（無 dev 依賴）可在純 Python 標準函式庫下運作
- [ ] 若需要第三方套件，在 `spec/` 中說明理由

---

### 3-05 Token 審計、實時計費與自動容災 (Token Auditing & Auto-Failover)

```
priority : HIGH
effort   : L
depends  : PHASE 1
```

- [ ] 實作執行緒安全的 `accounts.json` 多帳戶管理結構與併發鎖
- [ ] 在 LLM Provider Callbacks 實作實時計費與 token (prompt/completion/total) 統計
- [ ] 實作 Auto-Failover 機制：呼叫前判斷剩餘額度，超限時自動切換至下一個可用帳戶

---

### 3-06 Schema 嚴格校驗層 (Strict Schema Validation Layer)

```
priority : MEDIUM
effort   : S
depends  : 2-02
```

- [ ] 導入 `pydantic` 或等效函式庫，對所有 YAML 轉入的 Dict 執行強型別約束
- [ ] 針對 `skill.json` 與 `workflow.json` 實作 Schema 靜態驗證器

---

## PHASE 4 — Ecosystem / 生態系

### 4-01 GitHub Actions CI

```
priority : HIGH
effort   : S
depends  : 3-01
```

- [x] 建立 `.github/workflows/ci.yml`
- [x] CI 流程：lint → compile check → pytest → coverage report
- [x] 測試矩陣：Python 3.10 / 3.11 / 3.12，Ubuntu / macOS / Windows
- [x] 加入 badge 至 README（CI status、coverage、license）
- [x] PR 自動執行 `cli.py --validate` 檢查 `.agent/` 結構

---

### 4-02 Package 發布準備

```
priority : MEDIUM
effort   : M
depends  : 2-05, 4-01
```

- [ ] 確認 `pyproject.toml` 的 metadata 完整（name, version, description, author, license, classifiers）
- [ ] 建立 `CHANGELOG.md`（根目錄，面向使用者）
- [ ] 建立 `CONTRIBUTING.md`，說明如何貢獻 skill contract 或 runtime 實作
- [ ] 測試 `pip install -e .` 在乾淨環境的安裝流程
- [ ] 準備 PyPI 發布（若決定公開發布）
- [ ] 建立 GitHub Release 流程（tag-based）

---

### 4-03 PAP Registry（選用）

```
priority : LOW
effort   : XL
depends  : 4-02
```

- [ ] 設計 public skill registry 的 API 格式
- [ ] 建立 `registry/` 目錄，放置社群貢獻的 skill contract
- [ ] 定義 skill 發布與審查流程
- [ ] CLI 加入 `--install-skill <id>` 指令，從 registry 安裝 skill
- [ ] CLI 加入 `--publish-skill <path>` 指令，發布 skill 至 registry

---

## PHASE 5 — Self-Evolution / 自我演進

### 5-01 Agent Self-Audit

```
priority : MEDIUM
effort   : M
depends  : 1-02, 3-01
```

- [ ] 定義 self-audit workflow：agent 定期檢查自身 `.agent/` 狀態
- [ ] 檢查項目：skill 版本是否過時、memory 是否達到清理閾值、workflow 是否有長期 pending 任務
- [ ] 自動產生 audit report 寫入 `.agent/memory/semantic/audit_log.json`
- [ ] 在發現問題時產生 task recommendation（建議人類執行哪個 task）

---

### 5-02 Knowledge Base 自動更新

```
priority : LOW
effort   : L
depends  : 1-02, 5-01
```

- [ ] 定義 knowledge extraction 規則：什麼樣的 episodic memory 值得升級為 semantic knowledge
- [ ] 實作 `KnowledgeBase.promote(episodic_entry_id)` —— 將 episodic 轉為 semantic
- [ ] 加入人工確認步驟：自動升級的條目需標記 `status: draft`，等待確認後才變 `stable`
- [ ] 補充測試與範例

---

### 5-03 Skill 自動生成草稿

```
priority : LOW
effort   : L
depends  : 0-03, 5-01
```

- [ ] 當 agent 呼叫了一個不在 registry 的 tool 時，自動產生 capability contract 草稿
- [ ] 草稿放入 `.agent/skills/drafts/`，標記 `status: draft`
- [ ] 草稿包含：根據呼叫行為推斷的 inputs / outputs / description
- [ ] 需人工審查確認後，才能移至正式 `.agent/skills/`

---

## Task Summary

| Phase | 任務數 | 預估規模 |
|-------|--------|----------|
| PHASE 0 Foundation | 7 tasks, 38 items | 基礎，優先完成 |
| PHASE 1 Protocol | 9 tasks, 49 items | 核心功能 |
| PHASE 2 DX | 6 tasks, 36 items | 開發者體驗 |
| PHASE 3 Quality | 5 tasks, 26 items | 品質保證 |
| PHASE 4 Ecosystem | 3 tasks, 16 items | 生態建設 |
| PHASE 5 Self-Evolution | 3 tasks, 12 items | 長期目標 |
| **Total** | **33 tasks** | **177 items** |

---

*此文件由 PAP Core Agent 管理。任何新增任務需符合 T-04 Protocol Evolution 流程。*  
*定期執行 5-01 Self-Audit 以更新各任務狀態。*
*當所有任務皆已完成，該檔案可以刪除*
