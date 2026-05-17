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

## Status / 目前狀態

The repository currently includes a working Python reference runtime, layout
validation, layout discovery, CLI entrypoint, tool router, and tests for the
declared `.agent/` structure.

目前 repository 已包含可運作的 Python reference runtime、layout validation、
layout discovery、CLI entrypoint、tool router，以及針對 `.agent/` 宣告結構的測試。
