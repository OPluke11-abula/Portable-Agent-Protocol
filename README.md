# Portable-Agent-Protocol

Portable-Agent-Protocol (PAP) is a portable `.agent/` workspace protocol and a
reference runtime for AI-assisted projects. It gives agents and humans a shared,
versioned contract for tools, prompts, memory, workflows, project knowledge, and
runtime layout.

## English

### Current Status

This repository currently contains:

- A Python reference runtime in `agent_runtime/`.
- A Python CLI entrypoint in `cli.py`.
- A portable `.agent/` protocol workspace.
- JSON Schema validation for `.agent/agent.md`.
- Local tool routing for `search_web`, `query_db`, and `code_executor`.
- MCP server sync and execution bridge support.
- Pluggable memory backends: in-memory, JSON file, SQLite, and a vector backend placeholder.
- Markdown-frontmatter workflow DAG execution.
- A lightweight TypeScript runtime prototype in `agent_runtime_ts/`.
- VS Code extension tooling in `vscode-extension/`.
- Conformance and certification documents in `conformance/`.

The Python runtime is the primary implementation. The TypeScript runtime is a
lightweight prototype and does not yet provide the full validation and workflow
surface of the Python runtime.

### Repository Layout

```text
.
|-- .agent/                 # Portable protocol workspace
|   |-- agent.md            # Executable manifest and source of truth
|   |-- README.md           # Protocol workspace overview
|   |-- skills.md           # Skill registry
|   |-- prompts.md          # Prompt registry
|   |-- memory.md           # Memory contract
|   |-- workflows.md        # Workflow registry
|   |-- core/               # Runtime component contracts
|   |-- skills/             # Per-tool skill contracts
|   |-- prompts/            # Prompt guidance
|   |-- memory/             # Memory strategy notes
|   |-- workflows/          # Workflow DAG documents
|   `-- knowledge_base/     # Durable project knowledge
|-- agent_runtime/          # Python reference runtime
|-- agent_runtime_ts/       # TypeScript prototype runtime
|-- conformance/            # Compatibility and certification assets
|-- docs/                   # Whitepaper, hub spec, and talks
|-- examples/               # Runtime and integration examples
|-- schemas/                # JSON Schema for agent manifests
|-- tests/                  # Python test suite
|-- vscode-extension/       # VS Code extension source
|-- cli.py                  # CLI entrypoint
|-- pyproject.toml          # Python packaging and test config
`-- USAGE.md                # Copying `.agent/` into another project
```

### Architecture

PAP is organized around a three-layer `.agent/` contract:

1. Manifest layer: `.agent/agent.md` is the executable source of truth. The
   runtime reads its YAML front matter to load protocol version, runtime version,
   tools, MCP servers, memory settings, and declared paths.
2. Entry document layer: top-level `.agent/*.md` files are stable runtime-facing
   registries and contracts for skills, prompts, memory, and workflows.
3. Detail directory layer: `.agent/*/` directories provide deeper contracts,
   rationale, templates, and long-lived project knowledge.

The Python runtime keeps this protocol and executable behavior aligned:

- `agent_runtime.engine.AgentEngine` loads the manifest, validates schema and
  declared paths, discovers layout metadata, initializes memory, and owns the router.
- `agent_runtime.router.Router` registers importable local tools and can route
  configured MCP tool names.
- `agent_runtime.memory` provides replaceable memory backends.
- `agent_runtime.workflow.WorkflowExecutor` loads workflow DAGs from Markdown
  front matter and executes steps in dependency order.
- `agent_runtime.mcp_bridge` connects PAP skill contracts to MCP stdio servers.

### Installation

Use Python 3.10 or newer.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

MSYS or Unix-style Python on Windows may create `.venv/bin/python.exe` instead:

```powershell
.\.venv\bin\python.exe -m pip install -e ".[dev]"
```

macOS or Linux:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

### Validation and Tests

Run the test suite:

```bash
python -m pytest
```

Run the built-in validator:

```bash
python cli.py validate
```

Run a compile check:

```bash
python -m compileall cli.py agent_runtime tests
```

### CLI Usage

Initialize a `.agent/` workspace in the current directory:

```bash
python cli.py init
```

Show parsed manifest configuration:

```bash
python cli.py --show-config
```

Validate the current `.agent/` workspace:

```bash
python cli.py validate
```

Start the runtime:

```bash
python cli.py
```

Invoke a local tool:

```bash
python cli.py --tool search_web --params "{\"query\":\"portable agents\",\"limit\":3}"
```

Sync MCP server tools into `.agent/skills/` contracts:

```bash
python cli.py mcp sync
```

Pack the local `.agent/` profile for sharing:

```bash
python cli.py hub pack
```

Clone a public profile that contains a `.agent/` directory:

```bash
python cli.py hub clone owner/repository
```

### Runtime Example

```python
from agent_runtime import AgentEngine

engine = AgentEngine(".agent/agent.md")
print(engine.config["name"])
print(engine.layout["entrypoints"])
print(engine.router.available_tools)

result = engine.run("search_web", {"query": "Portable Agent Protocol"})
print(result)
```

### Workflow Example

Workflow files live under `.agent/workflows/` and store executable DAG metadata
in YAML front matter.

```python
from agent_runtime import AgentEngine

engine = AgentEngine(".agent/agent.md")
context = engine.execute_workflow("run_and_explain", {"code": "print('hello')"})
print(context)
```

### MCP Integration

MCP servers are declared in `.agent/agent.md` under `mcp_servers`.

- `python cli.py mcp sync` connects to configured servers and generates Markdown
  skill contracts in `.agent/skills/`.
- Runtime calls using the `mcp_<server>_<tool>` naming convention are forwarded
  to the matching MCP stdio server.

### Memory Backends

`agent_runtime.memory.create_memory_backend()` supports:

- `in_memory`: process-local ephemeral memory.
- `local` or `json`: JSON file persistence.
- `sqlite`: SQLite persistence.
- `vector`: placeholder backend for future semantic search integration.

The JSON backend does not create `memory.json` until a write operation occurs.

### VS Code Extension

The VS Code extension source is in `vscode-extension/`. It contributes:

- `PAP: Initialize Workspace`
- `PAP: Sync MCP Servers`
- YAML validation for `.agent/agent.md` through the published schema URL

### Conformance

The `conformance/` directory documents compatibility expectations for other
runtimes:

- `conformance/README.md`
- `conformance/CERTIFICATION.md`
- `conformance/layout-validation.yaml`
- `conformance/schema-validation.yaml`

### Source of Truth

When files overlap, use this priority order:

1. `.agent/agent.md` YAML front matter.
2. Top-level `.agent/*.md` entry documents.
3. Detailed `.agent/*/` directory documents.
4. Runtime implementation in `agent_runtime/`.
5. Repository-level docs such as this README and `USAGE.md`.

### Maintenance Rules

When adding a new local tool:

1. Add the runtime module under `agent_runtime/tools/<tool_name>.py`.
2. Add the skill contract under `.agent/skills/<tool_name>.md`.
3. Add the tool name to `.agent/agent.md`.
4. Add or update tests in `tests/`.
5. Run `python cli.py validate` and `python -m pytest`.

When changing protocol layout:

1. Update `.agent/agent.md`.
2. Update the matching `.agent/*.md` registry.
3. Update detailed docs under `.agent/*/`.
4. Update schema or conformance files if the change affects other runtimes.
5. Update tests and README if behavior or usage changes.

## 中文

### 目前狀態

這個 repository 目前包含：

- `agent_runtime/`：Python 參考 runtime。
- `cli.py`：Python CLI 入口。
- `.agent/`：可攜式 agent 協作協定工作區。
- `schemas/agent-schema.json`：用來驗證 `.agent/agent.md` 的 JSON Schema。
- 本地工具路由：`search_web`、`query_db`、`code_executor`。
- MCP server 同步與執行 bridge。
- 可替換記憶體後端：in-memory、JSON file、SQLite、vector placeholder。
- 以 Markdown front matter 定義的 workflow DAG 執行器。
- `agent_runtime_ts/`：輕量 TypeScript runtime prototype。
- `vscode-extension/`：VS Code extension tooling。
- `conformance/`：相容性與認證文件。

Python runtime 是目前主要且較完整的實作。TypeScript runtime 仍是輕量
prototype，尚未提供 Python runtime 的完整驗證與 workflow 功能面。

### Repository 結構

```text
.
|-- .agent/                 # 可攜式協定工作區
|   |-- agent.md            # 可執行 manifest 與主要真相來源
|   |-- README.md           # 協定工作區總覽
|   |-- skills.md           # Skill registry
|   |-- prompts.md          # Prompt registry
|   |-- memory.md           # Memory contract
|   |-- workflows.md        # Workflow registry
|   |-- core/               # Runtime 元件契約
|   |-- skills/             # 各工具的 skill contract
|   |-- prompts/            # Prompt 撰寫指引
|   |-- memory/             # Memory 策略說明
|   |-- workflows/          # Workflow DAG 文件
|   `-- knowledge_base/     # 長期專案知識
|-- agent_runtime/          # Python 參考 runtime
|-- agent_runtime_ts/       # TypeScript prototype runtime
|-- conformance/            # 相容性與認證資產
|-- docs/                   # Whitepaper、Hub spec、talk 文件
|-- examples/               # Runtime 與整合範例
|-- schemas/                # Agent manifest JSON Schema
|-- tests/                  # Python 測試
|-- vscode-extension/       # VS Code extension 原始碼
|-- cli.py                  # CLI 入口
|-- pyproject.toml          # Python package 與測試設定
`-- USAGE.md                # 如何複製 `.agent/` 到其他專案
```

### 架構

PAP 使用三層 `.agent/` 契約：

1. Manifest 層：`.agent/agent.md` 是可執行的主要真相來源。runtime 會讀取
   YAML front matter，取得 protocol version、runtime version、工具、MCP
   servers、memory 設定，以及宣告的路徑。
2. Entry document 層：最上層的 `.agent/*.md` 是 runtime 會面對的穩定
   registry 與 contract，包含 skills、prompts、memory、workflows。
3. Detail directory 層：`.agent/*/` 目錄提供更細的契約、設計理由、模板與長期專案知識。

Python runtime 的主要責任：

- `agent_runtime.engine.AgentEngine`：讀取 manifest、驗證 schema 和宣告路徑、探索 layout、初始化 memory、持有 router。
- `agent_runtime.router.Router`：註冊可 import 的本地工具，並可依設定路由 MCP 工具。
- `agent_runtime.memory`：提供可替換的 memory backend。
- `agent_runtime.workflow.WorkflowExecutor`：從 Markdown front matter 讀取 workflow DAG，依 dependency order 執行。
- `agent_runtime.mcp_bridge`：把 PAP skill contract 與 MCP stdio server 串接起來。

### 安裝

需要 Python 3.10 或更新版本。

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

如果 Windows 上使用 MSYS 或 Unix-style Python，venv 可能會建立在 `.venv/bin/python.exe`：

```powershell
.\.venv\bin\python.exe -m pip install -e ".[dev]"
```

macOS 或 Linux：

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

### 驗證與測試

執行完整 Python 測試：

```bash
python -m pytest
```

執行內建 validator：

```bash
python cli.py validate
```

執行 Python compile check：

```bash
python -m compileall cli.py agent_runtime tests
```

### CLI 使用方式

在目前目錄建立 `.agent/` 工作區：

```bash
python cli.py init
```

顯示解析後的 manifest 設定：

```bash
python cli.py --show-config
```

驗證目前 `.agent/` 工作區：

```bash
python cli.py validate
```

啟動 runtime：

```bash
python cli.py
```

呼叫本地工具：

```bash
python cli.py --tool search_web --params "{\"query\":\"portable agents\",\"limit\":3}"
```

將 MCP server 工具同步成 `.agent/skills/` contract：

```bash
python cli.py mcp sync
```

打包本地 `.agent/` profile：

```bash
python cli.py hub pack
```

複製包含 `.agent/` 的公開 profile：

```bash
python cli.py hub clone owner/repository
```

### Runtime 範例

```python
from agent_runtime import AgentEngine

engine = AgentEngine(".agent/agent.md")
print(engine.config["name"])
print(engine.layout["entrypoints"])
print(engine.router.available_tools)

result = engine.run("search_web", {"query": "Portable Agent Protocol"})
print(result)
```

### Workflow 範例

Workflow 文件放在 `.agent/workflows/`，可執行的 DAG metadata 放在 YAML front matter。

```python
from agent_runtime import AgentEngine

engine = AgentEngine(".agent/agent.md")
context = engine.execute_workflow("run_and_explain", {"code": "print('hello')"})
print(context)
```

### MCP 整合

MCP servers 在 `.agent/agent.md` 的 `mcp_servers` 宣告。

- `python cli.py mcp sync` 會連到設定的 servers，並在 `.agent/skills/` 產生 Markdown skill contracts。
- runtime 呼叫符合 `mcp_<server>_<tool>` 命名格式的工具時，會轉送到對應 MCP stdio server。

### Memory Backends

`agent_runtime.memory.create_memory_backend()` 支援：

- `in_memory`：process-local 暫存記憶體。
- `local` 或 `json`：JSON file persistence。
- `sqlite`：SQLite persistence。
- `vector`：未來 semantic search integration 的 placeholder。

JSON backend 不會在初始化時建立 `memory.json`，第一次寫入時才會建立檔案。

### VS Code Extension

VS Code extension 原始碼位於 `vscode-extension/`，目前提供：

- `PAP: Initialize Workspace`
- `PAP: Sync MCP Servers`
- 透過公開 schema URL 驗證 `.agent/agent.md`

### Conformance

`conformance/` 目錄記錄其他 runtime 的相容性期待：

- `conformance/README.md`
- `conformance/CERTIFICATION.md`
- `conformance/layout-validation.yaml`
- `conformance/schema-validation.yaml`

### 真相來源順序

當文件內容有重疊時，依照以下順序判斷：

1. `.agent/agent.md` YAML front matter。
2. 最上層 `.agent/*.md` entry documents。
3. `.agent/*/` 詳細文件。
4. `agent_runtime/` runtime 實作。
5. Repository 層級文件，例如本 README 與 `USAGE.md`。

### 維護規則

新增本地工具時：

1. 在 `agent_runtime/tools/<tool_name>.py` 新增 runtime module。
2. 在 `.agent/skills/<tool_name>.md` 新增 skill contract。
3. 在 `.agent/agent.md` 加入工具名稱。
4. 在 `tests/` 新增或更新測試。
5. 執行 `python cli.py validate` 與 `python -m pytest`。

修改 protocol layout 時：

1. 更新 `.agent/agent.md`。
2. 更新對應的 `.agent/*.md` registry。
3. 更新 `.agent/*/` 內的詳細文件。
4. 如果會影響其他 runtime，更新 schema 或 conformance 文件。
5. 如果行為或使用方式改變，更新測試與 README。
