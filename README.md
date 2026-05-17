# Portable-Agent-Protocol

Portable-Agent-Protocol is a portable `.agent/` collaboration protocol plus a
Python reference runtime. It is designed for projects that want AI agents to
share a stable workspace contract for tools, prompts, memory, workflows, and
long-lived project knowledge.

Portable-Agent-Protocol 是一個可攜式 `.agent/` 協作協定，加上一個 Python
reference runtime。它的目標是讓專案能用穩定的工作區契約，讓 AI agents
共同理解 tools、prompts、memory、workflows，以及長期專案知識。

## Project Scope / 專案定位

This repository is not only a documentation template, and it is not only a
Python runtime. It combines both parts:

- `.agent/`: the protocol layer and portable collaboration workspace
- `agent_runtime/`: the Python reference implementation for that protocol
- `tests/`: regression tests that keep the protocol layout and runtime aligned
- `examples/`: examples for protocol writeback and runtime simulation
- `USAGE.md`: guidance for copying `.agent/` into another project

這個 repository 不是單純的文件模板，也不是單純的 Python runtime。它是兩者的整合：

- `.agent/`：協定層與可攜式協作工作區
- `agent_runtime/`：此協定的 Python reference implementation
- `tests/`：確保協定 layout 與 runtime 維持一致的回歸測試
- `examples/`：protocol writeback 與 runtime simulation 範例
- `USAGE.md`：將 `.agent/` 複製到其他專案的使用說明

## 🌟 Key Features / 新增亮點

### 1. Model Context Protocol (MCP) Integration
The Python runtime includes `pap-mcp-bridge`, seamlessly connecting PAP with external MCP servers.
- **Sync**: Run `python cli.py mcp sync` to dynamically generate Markdown contracts (`.agent/skills/*.md`) from MCP JSON Schemas.
- **Execute**: The `AgentEngine` router dynamically forwards tool calls directly to the underlying MCP servers via stdio.

### 2. VS Code Extension (Dev Tooling)
PAP comes with an official VS Code extension (`vscode-extension/`) that provides:
- **IntelliSense**: Real-time YAML schema validation and auto-complete for `agent.md`.
- **UI Commands**: 1-click workspace initialization (`PAP: Initialize Workspace`) and MCP sync (`PAP: Sync MCP Servers`).

### 1. MCP 雙向橋接 (Model Context Protocol)
Python runtime 內建了 `pap-mcp-bridge`，無縫銜接外部 MCP 伺服器：
- **同步 (Sync)**：執行 `python cli.py mcp sync` 自動將 MCP 的 JSON Schema 轉譯為標準的 Markdown 工具合約 (`.agent/skills/*.md`)。
- **動態執行 (Execute)**：`AgentEngine` 路由會自動攔截 MCP 工具呼叫，並透過 stdio 轉發給底層 MCP Server。

### 2. VS Code 開發工具鏈
PAP 提供了專屬的 VS Code 擴充套件 (`vscode-extension/`)：
- **智慧提示 (IntelliSense)**：為 `agent.md` 提供即時的 YAML Schema 驗證與自動完成提示。
- **UI 捷徑**：提供一鍵生成工作區 (`PAP: Initialize Workspace`) 與同步 MCP (`PAP: Sync MCP Servers`) 功能。

## Architecture / 架構

The `.agent/` workspace has three layers.

`.agent/` 工作區分為三層。

### Layer 1: Manifest / 第一層：Manifest

`.agent/agent.md` is the executable source of truth. The Python runtime reads
the YAML front matter in this file to determine runtime configuration, enabled
tools, and declared protocol paths.

`.agent/agent.md` 是 executable source of truth。Python runtime 會讀取這個檔案
的 YAML front matter，用來決定 runtime configuration、啟用的 tools，以及協定
宣告的路徑。

### Layer 2: Runtime Entry Documents / 第二層：Runtime Entry Documents

The top-level `.agent/*.md` files are stable runtime-facing contracts and
registries:

- `.agent/skills.md`: skill registry and runtime module map
- `.agent/prompts.md`: prompt catalog and reusable prompt snippets
- `.agent/memory.md`: memory backend and persistence contract
- `.agent/workflows.md`: workflow registry and expected workflow behavior

頂層 `.agent/*.md` 檔案是 runtime-facing contracts 與 registries：

- `.agent/skills.md`：skill registry 與 runtime module map
- `.agent/prompts.md`：prompt catalog 與可重用 prompt snippets
- `.agent/memory.md`：memory backend 與 persistence contract
- `.agent/workflows.md`：workflow registry 與 workflow 行為契約

### Layer 3: Detailed Directories / 第三層：詳細目錄

Subdirectories provide deeper contracts, rationale, templates, and guidance:

- `.agent/core/`: engine, router, and logger responsibilities
- `.agent/skills/`: per-skill contracts and safety notes
- `.agent/prompts/`: prompt-authoring and error-handling guidance
- `.agent/memory/`: memory strategy notes
- `.agent/workflows/`: per-workflow notes and usage guidance
- `.agent/knowledge_base/`: durable project knowledge

子目錄負責更細的 contracts、設計理由、templates 與 guidance：

- `.agent/core/`：engine、router、logger 的責任定義
- `.agent/skills/`：每個 skill 的 contract 與 safety notes
- `.agent/prompts/`：prompt 撰寫與錯誤處理 guidance
- `.agent/memory/`：memory strategy notes
- `.agent/workflows/`：每個 workflow 的補充 note 與使用 guidance
- `.agent/knowledge_base/`：長期穩定的專案知識

## Repository Layout / Repository 結構

```text
.
|-- .agent/
|   |-- agent.md
|   |-- README.md
|   |-- skills.md
|   |-- prompts.md
|   |-- memory.md
|   |-- workflows.md
|   |-- core/
|   |-- skills/
|   |-- prompts/
|   |-- memory/
|   |-- workflows/
|   `-- knowledge_base/
|-- agent_runtime/
|   |-- engine.py
|   |-- router.py
|   |-- logger.py
|   `-- tools/
|-- tests/
|-- examples/
|-- cli.py
|-- pyproject.toml
`-- USAGE.md
```

## Runtime Behavior / Runtime 行為

The current Python reference runtime:

- parses `.agent/agent.md` YAML front matter
- validates declared protocol paths
- validates that each declared tool has a matching `.agent/skills/<tool>.md`
  contract
- discovers the declared `.agent/` layout and exposes it as
  `AgentEngine.layout`
- routes tool calls through `agent_runtime.router.Router`

目前 Python reference runtime 會：

- 解析 `.agent/agent.md` 的 YAML front matter
- 驗證宣告的 protocol paths 是否存在
- 驗證每個宣告 tool 是否都有對應的 `.agent/skills/<tool>.md` contract
- discover 宣告的 `.agent/` layout，並透過 `AgentEngine.layout` 暴露給 runtime
- 透過 `agent_runtime.router.Router` 路由 tool calls

Example:

```python
from agent_runtime import AgentEngine

engine = AgentEngine(".agent/agent.md")
print(engine.config["name"])
print(engine.layout["entrypoints"])
print(engine.router.available_tools)
```

## Installation / 安裝

Use Python 3.10 or newer.

請使用 Python 3.10 或更新版本。

```text
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

On macOS or Linux:

```text
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## Testing / 測試

Run the full test suite:

執行完整測試：

```text
python -m pytest
```

Run a compile check:

執行 compile check：

```text
python -m compileall cli.py agent_runtime tests
```

## CLI Usage / CLI 使用

Show the parsed manifest config:

顯示解析後的 manifest config：

```text
python cli.py --show-config
```

Validate the `.agent/` workspace against the schema:

驗證 `.agent/` 工作區是否符合 Schema：

```text
python cli.py validate
```

Start the runtime with the default manifest:

用預設 manifest 啟動 runtime：

```text
python cli.py
```

Invoke a tool:

呼叫 tool：

```text
python cli.py --tool search_web --params "{\"query\":\"portable agents\"}"
```

## Protocol Evolution Rules / 協定演進規則

When adding or changing a capability, keep the protocol and runtime aligned.

新增或修改 capability 時，必須同步維持 protocol 與 runtime 一致。

- New runtime capability: update `.agent/agent.md`, `.agent/skills.md`,
  `.agent/skills/<tool>.md`, runtime code, and tests.
- New prompt policy: update `.agent/prompts.md` if it affects runtime-facing
  behavior, and `.agent/prompts/` for detailed guidance.
- New workflow: update `.agent/workflows.md` and add or update a document under
  `.agent/workflows/`.
- New memory behavior: update `.agent/memory.md` for runtime-facing contract
  changes, and `.agent/memory/` for detailed strategy notes.
- New durable project knowledge: update `.agent/knowledge_base/`.

- 新 runtime capability：同步更新 `.agent/agent.md`、`.agent/skills.md`、
  `.agent/skills/<tool>.md`、runtime code 與 tests。
- 新 prompt policy：若影響 runtime-facing behavior，更新 `.agent/prompts.md`；
  詳細 guidance 則更新 `.agent/prompts/`。
- 新 workflow：更新 `.agent/workflows.md`，並在 `.agent/workflows/` 新增或更新文件。
- 新 memory behavior：runtime-facing contract 更新 `.agent/memory.md`；詳細策略更新
  `.agent/memory/`。
- 新長期專案知識：更新 `.agent/knowledge_base/`。

## Source of Truth / Source of Truth

Use this priority order when documents overlap:

當文件內容重疊時，依照以下優先順序判斷：

1. `.agent/agent.md`: executable runtime source of truth
2. top-level `.agent/*.md`: runtime-facing contracts and registries
3. `.agent/*/` directories: detailed guidance, rationale, templates, and notes
4. `agent_runtime/`: Python reference implementation that must stay consistent
   with the protocol contract

## 🚀 Roadmap & Strategy / 戰略藍圖與路線圖

### Project Status / 專案現況總結

**Current Strengths / 現有強項:**
- **Clear Three-Layer Architecture**: Manifest → Runtime Entry Documents → Detailed Directories. (三層架構設計清晰，職責明確)
- **Protocol-First Design**: `.agent/agent.md` as Single Source of Truth. (協定優先，降低與特定 runtime 的耦合)
- **Validation**: Layout Validation + Tool Contract verification. (確保協定文件與 runtime 代碼不脫節)
- **Bilingual Support**: Friendly to local and international communities. (中英雙語，兼顧在地與國際推廣)
- **Engineering Standardization**: pyproject.toml, pytest, CLI entrypoint. (工程標準化，易於維護)
- **Unique Philosophy**: "Documentation as Protocol" - readable by both AI and humans. (設計哲學獨特：「文件即協定」)

**Current Weaknesses / 現有弱點:**
- **No Schema Versioning**: Lack of a formal versioning mechanism (semver). (協定格式缺乏正式版本號機制)
- **Python-only Runtime**: Limits adoption in JS/TS communities. (目前只有 Python runtime)
- **Declarative Memory**: Lacks an executable persistence backend. (Memory contract 停留在聲明式，缺乏可執行的後端)
- **Document-based Workflows**: Workflows are not executable DAGs. (Workflow 是文件描述而非可執行圖)
- **Ambiguous Integrations**: Integration with LLM-Agent-System is not explicitly declared. (與 LLM-Agent-System 整合關係未明確)

### Optimization Roadmap / 優化路線圖

#### Phase 1: Protocol Maturation (0-3 Months) / 第一階段：協定成熟化（0–3 個月）
1. **Schema Versioning / 協定版本化**: Add protocol versioning and semver rules to make PAP a trusted standard.
2. **JSON Schema & CLI Validator**: Implement `pap validate` CLI to make the protocol machine-verifiable.
3. **Memory Backend Abstractions / Memory Contract 實作化**: Implement replaceable memory backends (InMemory, SQLite, VectorDB).

#### Phase 2: Ecosystem Building (3-6 Months) / 第二階段：生態建設（3–6 個月）
4. **Workflow Execution Engine / Workflow 執行引擎**: Introduce DAG-driven workflow scheduling for true protocol-driven execution.
5. **Cross-Language Runtime / 跨語言 Runtime 實作**: Build a TypeScript reference runtime and a Conformance Test Suite.
6. **.agent/ Hub / 協定分享平台**: Launch a public platform to share Agent Profiles, skills, and prompts.

#### Phase 3: Standardization (6-12 Months) / 第三階段：標準化競爭（6–12 個月）
7. **Competitive Differentiation / 對標分析與差異化定位**: Position PAP clearly as the "AI-Native Workspace Protocol" compared to Anthropic MCP (tools) and Google A2A (communication).
8. **Whitepaper & Community / 技術白皮書與社群佈局**: Publish a technical whitepaper and establish thought leadership.
9. **Official LAS Integration / 正式整合 LLM-Agent-System**: Establish LAS as the official reference application.

### Protocol Architecture Evolution / 協定架構演進圖

```text
Current (v0.x — Exploration)
└── Markdown + YAML front matter | Python-only | Declarative memory | Document workflow

↓ Phase 1

v1.0 (Stability)
└── Semver versioning | CLI validator | Memory Backend | PAP-LAS integration

↓ Phase 2

v1.x (Ecosystem)
└── Workflow DAG | TypeScript Runtime | Conformance Test Suite

↓ Phase 3

v2.0 (Standardization)
└── .agent/ Hub | Whitepaper | Multi-language runtimes | Community standard
```

```text
現在（v0.x — 探索期）
└── Markdown + YAML front matter | Python-only | 聲明式 memory | 文件式 workflow

↓ 第一階段

v1.0（協定穩定期）
└── 版本化 semver | CLI validator | Memory Backend 實作 | PAP-LAS 整合宣告

↓ 第二階段

v1.x（生態建設期）
└── Workflow DAG 執行 | TypeScript Runtime | Conformance Test Suite

↓ 第三階段

v2.0（標準競爭期）
└── .agent/ Hub 上線 | 白皮書發布 | 多語言 runtime 生態 | 社群標準地位
```

### Market Opportunity & Strategy / 市場機會與戰略定位

PAP occupies a unique "Protocol Layer" between foundation models and heavy application frameworks. Our strategic moats include:
1. **First-Mover Advantage / 先發優勢**: Establishing mindshare for the `.agent/` workspace.
2. **Network Effects / 網絡效應**: A growing ecosystem on the Hub increases value.
3. **Standard Stickiness / 標準粘性**: High migration cost once adopted in production.

PAP 佔據了「基礎模型 API」與「應用框架」之間的「協定層（Protocol Layer）」空白地帶，主要護城河包含先發優勢、生態網絡效應與標準粘性。

### Top 3 Priorities / 最優先的三件事

1. **Schema Versioning + CLI Validator / 實作協定版本化 + 發布 CLI validator**: The foundational requirement for community trust. (被社區嚴肅對待的最小門票)
2. **Memory Backend Abstraction / 實作 Memory Backend 抽象層**: Transitioning memory from declarative to executable. (從「理念」變成「工具」的關鍵)
3. **Whitepaper & Tech Talks / 發布技術白皮書並在社群演講**: Spreading the "Documentation as Protocol" philosophy. (傳播差異化哲學)

## Status / 目前狀態

The repository currently includes a working Python reference runtime, layout
validation, layout discovery, CLI entrypoint, tool router, and tests for the
declared `.agent/` structure.

目前的 repository 已包含可運作的 Python runtime、MCP 雙向橋接器 (pap-mcp-bridge)、以及 VS Code 擴充套件。我們成功將 PAP 推升為一個可被機器驗證、具備強大開發工具鏈的企業級標準。
