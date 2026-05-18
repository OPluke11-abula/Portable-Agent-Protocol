# Portable Agent Protocol (PAP)

[![PAP Compatible](https://img.shields.io/badge/PAP--Compatible-blue.svg)](https://github.com/OPluke11-abula/Portable-Agent-Protocol)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)]()

*(For Traditional Chinese, please scroll down. / 中文說明請見下方)*

The **Portable Agent Protocol (PAP)** is a standardized, framework-agnostic definition for AI agent workspaces. It separates the "Agent's Brain and Identity" from the "Runtime Execution Engine," allowing you to build an agent once and run it anywhere.

By standardizing how prompts, tools, workflows, and memory are defined, PAP solves the vendor lock-in problem common in today's highly fragmented AI agent framework ecosystem.

---

## 📖 Key Features

### 1. Framework Agnostic Workspace (`.agent/`)
PAP defines the `.agent/` directory as the universal manifest for any AI agent. It contains:
- `agent.md`: The central configuration and YAML front-matter manifest.
- `persona.md`: The agent's identity, tone, and core directives.
- `skills/`: Standardized markdown definitions for external tools and APIs.
- `workflows/`: Executable Directed Acyclic Graph (DAG) workflow definitions.
- `memory.md`: Definitions for memory backends and persistence schemas.

### 2. Built-in MCP (Model Context Protocol) Bridge
PAP natively supports Anthropic's **Model Context Protocol (MCP)**.
Using the CLI (`pap mcp sync`), PAP can automatically discover tools from any MCP server and generate local markdown skill contracts inside the `.agent/skills/` directory.

### 3. Pluggable Memory Backends
The reference runtime ships with a fully pluggable memory interface. Switch between `InMemory`, `JSONFile`, `SQLite`, or semantic `VectorDB` backends simply by changing the `memory.backend` string in your `agent.md`.

### 4. Cross-Language Runtimes
PAP is not restricted to Python. This repository provides:
- `agent_runtime/`: The fully-featured Python execution engine.
- `agent_runtime_ts/`: A lightweight TypeScript execution engine for the Node.js/JS ecosystem.

### 5. The `.agent/ Hub` Ecosystem
Stop building agents from scratch. The Hub is a Git-backed public registry where you can discover, download, and share agent profiles securely.
- **Clone:** `python cli.py hub clone username/agent-name`
- **Publish:** `python cli.py hub pack` (Securely archives your workspace, stripping out private `memory/` and `.env` files).

---

## 🚀 Getting Started

### Installation
Clone this repository and optionally install the Python reference runtime.
```bash
git clone https://github.com/OPluke11-abula/Portable-Agent-Protocol.git
cd Portable-Agent-Protocol
pip install -e .
```

### CLI Usage
PAP provides a robust CLI (`cli.py`) for managing your workspaces.

1. **Initialize a new workspace:**
   ```bash
   python cli.py init
   ```
2. **Validate your workspace schema:**
   ```bash
   python cli.py validate
   ```
3. **Sync tools from an MCP server:**
   ```bash
   python cli.py mcp sync
   ```
4. **Clone a pre-built agent from the Hub:**
   ```bash
   python cli.py hub clone OPluke11-abula/my-agent-template
   ```

---

## 🎖 PAP-Compatible Certification

Build trust within the community by displaying the **PAP-Compatible Badge** on your framework.
To get certified, your runtime must:
1. Parse the schema correctly.
2. Resolve the `.agent/` directory layout.
3. Pass all language-agnostic tests in the `conformance/` directory.

> Read the full [Certification Rules](conformance/CERTIFICATION.md) and check out our official [Lightweight Agent System (LAS) Integration Example](examples/las-integration/).

---
---

# Portable Agent Protocol (PAP) - 繁體中文

[![PAP Compatible](https://img.shields.io/badge/PAP--Compatible-blue.svg)](https://github.com/OPluke11-abula/Portable-Agent-Protocol)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)]()

**Portable Agent Protocol (PAP)** 是一個標準化、與框架無關的 AI Agent 工作區定義協定。它將「Agent 的大腦與身份」與「底層執行引擎」徹底解耦，讓您只需打造一次 Agent，即可在任何框架或平台上執行。

透過標準化提示詞 (Prompts)、工具 (Tools)、工作流 (Workflows) 與記憶體 (Memory) 的定義方式，PAP 解決了當今 AI Agent 框架生態系中嚴重的「供應商鎖定 (Vendor Lock-in)」問題。

---

## 📖 核心亮點

### 1. 跨框架標準工作區 (`.agent/`)
PAP 將 `.agent/` 目錄定義為所有 AI Agent 的通用配置檔，內部包含：
- `agent.md`：核心設定檔與 YAML Manifest。
- `persona.md`：定義 Agent 的人格、語氣與核心原則。
- `skills/`：以 Markdown 定義的外部工具與 API 合約。
- `workflows/`：可執行的 DAG (有向無環圖) 工作流定義。
- `memory.md`：記憶體後端與持久化架構的定義。

### 2. 原生支援 MCP (Model Context Protocol) 橋接
PAP 原生支援 Anthropic 提出的 **Model Context Protocol (MCP)**。
透過 CLI (`pap mcp sync`)，PAP 能夠自動連線到任何 MCP Server，探索其提供的工具，並在 `.agent/skills/` 中自動生成對應的 Markdown 技能合約。

### 3. 可插拔記憶體架構 (Pluggable Memory)
官方 Runtime 內建了完整的抽象記憶體介面。開發者只需在 `agent.md` 中修改 `memory.backend` 的字串，即可一鍵切換 `InMemory` (記憶體內)、`JSONFile` (JSON 檔案)、`SQLite` (資料庫) 甚至語義檢索的 `VectorDB`。

### 4. 跨語言執行環境 (Cross-Language Runtimes)
PAP 並不侷限於 Python，本專案同時提供：
- `agent_runtime/`：功能完整的 Python 執行引擎參考實作。
- `agent_runtime_ts/`：輕量級的 TypeScript 執行引擎，專為 Node.js/JS 生態系打造。

### 5. `.agent/ Hub` 生態系
不需要每次都從頭打造 Agent。Hub 是一個基於 Git 的公開分享平台，讓您能安全地探索、下載與分享 Agent 配置。
- **下載 Agent：** `python cli.py hub clone username/agent-name`
- **發布 Agent：** `python cli.py hub pack`（自動將您的工作區打包，並基於資安考量，自動過濾掉私人的 `memory/` 目錄與 `.env` 變數檔）。

---

## 🚀 快速開始

### 安裝方式
請 Clone 本專案，並可選擇性安裝 Python 參考引擎。
```bash
git clone https://github.com/OPluke11-abula/Portable-Agent-Protocol.git
cd Portable-Agent-Protocol
pip install -e .
```

### CLI 工具使用
PAP 提供了強大的 CLI (`cli.py`) 來協助您管理工作區。

1. **初始化全新工作區：**
   ```bash
   python cli.py init
   ```
2. **驗證工作區結構與 Schema：**
   ```bash
   python cli.py validate
   ```
3. **從 MCP Server 同步工具：**
   ```bash
   python cli.py mcp sync
   ```
4. **從 Hub 下載現成的 Agent：**
   ```bash
   python cli.py hub clone OPluke11-abula/my-agent-template
   ```

---

## 🎖 PAP-Compatible 認證機制

我們鼓勵所有 AI 框架開發者在專案中掛上 **PAP-Compatible 徽章**，以建立社群信任。
要取得此認證，您的執行環境 (Runtime) 必須滿足：
1. 能夠正確解析 Schema 格式。
2. 能夠解析 `.agent/` 的目錄結構配置。
3. 必須通過 `conformance/` 目錄下所有的跨語言合規測試 (YAML 測試檔)。

> 請閱讀完整的 [認證規範 (Certification Rules)](conformance/CERTIFICATION.md)，並參考我們官方的 [Lightweight Agent System (LAS) 整合範例](examples/las-integration/)。
