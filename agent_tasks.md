# PAP Agent Task Queue
>
> Protocol: portable-agent-protocol v0.1.0  
> Format: PAP Task Contract v1  
> Status legend: `[ ]` pending · `[~]` in-progress · `[x]` done · `[!]` blocked

---

## PHASE 0 to 3 — Completed Milestones (Completed & Verified)
All tasks under Phase 0, 1, 2, and 3 have been fully implemented, tested, and validated with a 100% test pass rate (183/183 tests green).

| Phase | Task ID | Description | Status |
|---|---|---|---|
| **Phase 0** | 0-00 | 代理身份與引導配置 (.AGENT) | `[x]` Done |
| | 0-01 | Schema 正式化 | `[x]` Done |
| | 0-02 | Memory 格式落地 | `[x]` Done |
| | 0-03 | Skill Contract 標準化 | `[x]` Done |
| | 0-04 | Router 強化 | `[x]` Done |
| | 0-05 | CLI 完整化 | `[x]` Done |
| | 0-06 | Open Source Skills 引入與匿名化 | `[x]` Done |
| | 0-07 | Onboarding 順序性與強制性校驗 | `[x]` Done |
| | 0-08 | tool_manifest.py 整合與全局技能屏蔽 | `[x]` Done |
| **Phase 1** | 1-01 | Workflow 引擎實作 | `[x]` Done |
| | 1-02 | Knowledge Base 索引 | `[x]` Done |
| | 1-03 | Prompt Registry 可執行化 | `[x]` Done |
| | 1-04 | Cross-Agent Handoff 機制 | `[x]` Done |
| | 1-05 | Protocol Version Management | `[x]` Done |
| | 1-06 | 跨層級技能尋址與覆蓋機制 | `[x]` Done |
| | 1-07 | 命令行工作流斷點續傳支援 | `[x]` Done |
| | 1-08 | 自動化 Token 溢出偵測與交接觸發器 | `[x]` Done |
| | 1-09 | 工作流實體檔案 Checkpoint 匯出器 | `[x]` Done |
| **Phase 2** | 2-01 | Init 指令 | `[x]` Done |
| | 2-02 | Lint 指令 | `[x]` Done |
| | 2-03 | 多語言 Runtime 規格文件 | `[x]` Done |
| | 2-04 | 範例庫擴充 | `[x]` Done |
| | 2-05 | 文件網站結構 | `[x]` Done |
| | 2-06 | 腦手分離合規性靜態檢查 | `[x]` Done |
| **Phase 3** | 3-01 | 測試覆蓋率提升 | `[x]` Done |
| | 3-02 | 安全審查 | `[x]` Done |
| | 3-03 | 效能基準測試 | `[x]` Done |
| | 3-04 | Dependency 最小化 | `[x]` Done |
| | 3-05 | Token 審計、實時計費與自動容災 | `[x]` Done |
| | 3-06 | Schema 嚴格校驗層 | `[x]` Done |

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

- [x] 確認 `pyproject.toml` 的 metadata 完整（name, version, description, author, license, classifiers）
- [x] 建立 `CHANGELOG.md`（根目錄，面向使用者）
- [x] 建立 `CONTRIBUTING.md`，說明如何貢獻 skill contract 或 runtime 實作
- [x] 測試 `pip install -e .` 在乾淨環境的安裝流程
- [x] 準備 PyPI 發布（若決定公開發布）
- [x] 建立 GitHub Release 流程（tag-based）

---

### 4-03 PAP Registry（選用）

```
priority : LOW
effort   : XL
depends  : 4-02
```

- [x] 設計 public skill registry 的 API 格式
- [x] 建立 `registry/` 目錄，放置社群貢獻的 skill contract
- [x] 定義 skill 發布與審查流程
- [x] CLI 加入 `--install-skill <id>` 指令，從 registry 安裝 skill
- [x] CLI 加入 `--publish-skill <path>` 指令，發布 skill 至 registry

---

## PHASE 5 — Self-Evolution / 自我演進

### 5-01 Agent Self-Audit

```
priority : MEDIUM
effort   : M
depends  : 1-02, 3-01
```

- [x] 定義 self-audit workflow：agent 定期檢查自身 `.agent/` 狀態
- [x] 檢查項目：skill 版本是否過時、memory 是否達到清理閾值、workflow 是否有長期 pending 任務
- [x] 自動產生 audit report 寫入 `.agent/memory/semantic/audit_log.json`
- [x] 在發現問題時產生 task recommendation（建議人類執行哪個 task）

---

### 5-02 Knowledge Base 自動更新

```
priority : LOW
effort   : L
depends  : 1-02, 5-01
```

- [x] 定義 knowledge extraction 規則：什麼樣的 episodic memory 值得升級為 semantic knowledge
- [x] 實作 `KnowledgeBase.promote(episodic_entry_id)` —— 將 episodic 轉為 semantic
- [x] 加入人工確認步驟：自動升級的條目需標記 `status: draft`，等待確認後才變 `stable`
- [x] 補充測試與範例

---

### 5-03 Skill 自動生成草稿

```
priority : LOW
effort   : L
depends  : 0-03, 5-01
```

- [x] 當 agent 呼叫了一個不在 registry 的 tool 時，自動產生 capability contract 草稿
- [x] 草稿放入 `.agent/skills/drafts/`，標記 `status: draft`
- [x] 草稿包含：根據呼叫行為推斷的 inputs / outputs / description
- [x] 需人工審查確認後，才能移至正式 `.agent/skills/`

---

## PHASE 6 - LAS/PAP Workflow, Evidence Memory, and Review Gate Alignment

> Source plan: `D:\GitHub\LLM-Agent-System\docs\architecture\las-pap-collaboration-memory-security-plan.md`
> Handoff for next PAP thread: `C:\tmp\PAP_thread\handoff.md`
> Required onboarding: read `.agent/agent.md`, `.agent/skills.md`, `agent_tasks.md`, `.agent/handoff_guide.md`, then `.agent/routing.md` before execution.

### 6-01 PAP Workflow Governance Scaffold

```
priority : HIGH
effort   : M
depends  : 5-01
```

- [ ] Add lightweight workflow governance docs for source-of-truth order, risk policy, review protocol, and handoff schema.
- [ ] Ensure the docs preserve PAP's Brain and Hands decoupling and deterministic routing rules.
- [ ] Keep README free of internal task logs; update only protocol-facing docs unless a user-facing capability changes.

### 6-02 Workflow Manifest and Checkpoint Schemas

```
priority : HIGH
effort   : M
depends  : 6-01
```

- [ ] Add opt-in PAP workflow manifest schema for stages, directors, canonical artifacts, allowed actions, and approval policy.
- [ ] Add checkpoint schema with artifact hash, evidence refs, verifier, unresolved risks, and status.
- [ ] Keep all new schema fields backward compatible with existing PAP workspaces.

### 6-03 Read-Only Workflow Linter

```
priority : HIGH
effort   : M
depends  : 6-02
```

- [ ] Implement a read-only workflow linter that validates workflow manifests and checkpoints without executing stage actions.
- [ ] Reject missing required fields, workspace path escapes, invalid checkpoint status, and missing evidence refs where required.
- [ ] Add pytest coverage for valid, invalid, and backward-compatible workflow manifests.

### 6-04 Evidence Memory Schema Proposal

```
priority : MEDIUM
effort   : M
depends  : 6-02
```

- [ ] Define protocol fields for L0 raw evidence refs, L1 atoms, L2 scenarios, L3 persona/profile, Mermaid canvas refs, `node_id`, and `result_ref`.
- [ ] Require every summarized memory claim to trace back to raw evidence or a canonical artifact.
- [ ] Do not add automatic capture hooks, daemons, OpenClaw patches, or remote memory gateways.

### 6-05 Structured Review and Security Findings Schema

```
priority : HIGH
effort   : M
depends  : 6-02
```

- [ ] Add structured review/security findings schema with verdict, severity, source trace, impact, remediation, and validation status.
- [ ] Require high/critical findings to include both exploit path and impact.
- [ ] Keep security review report-only by default and do not enable parallel audit agents unless the user explicitly asks.

### 6-06 LAS Interop Validation Plan

```
priority : MEDIUM
effort   : S
depends  : 6-03, 6-04, 6-05
```

- [ ] Document how LAS will consume PAP workflow, checkpoint, evidence-ref, memory, and review-gate fields.
- [ ] Include compatibility checks for LAS `ConductorPlan`, `LongTermMemoryStore`, `UnifiedPolicyGate`, and `AuditLedger`.
- [ ] Provide exact verification commands for both PAP and LAS before declaring the protocol extension ready.

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
| PHASE 6 Workflow Alignment | 6 tasks, 18 items | Pending |
| **Total** | **39 tasks** | **195 items** |

---

*此文件由 PAP Core Agent 管理。任何新增任務需符合 T-04 Protocol Evolution 流程。*  
*定期執行 5-01 Self-Audit 以更新各任務狀態。*
*當所有任務皆已完成，該檔案可以刪除*
