# Portable Agent Protocol (PAP) Technical Whitepaper
## 攜帶式 Agent 協定技術白皮書

**Version:** 1.0.0
**Date:** May 2026

---

## 1. Abstract / 摘要

The AI Agent ecosystem is expanding rapidly, but it suffers from a critical missing piece: the **Protocol Layer**. Currently, developers are forced to choose between highly opinionated frameworks (like LangChain or LlamaIndex) that lock them into specific architectures, or raw APIs that provide no standard way to persist memory, tools, and workflows across sessions. 

The **Portable Agent Protocol (PAP)** fills this void. PAP is an "AI-Native Workspace Protocol" that uses a `.agent/` directory structure to store agent states, tools, and knowledge. Its core philosophy is **"Documentation as Protocol"**—using human-readable Markdown as the primary interface. This ensures that both humans and AI agents can seamlessly read, understand, and modify the agent's workspace, creating a truly portable and framework-agnostic environment.

AI Agent 生態系正快速擴張，但我們發現缺少了最關鍵的一環：「**協定層 (Protocol Layer)**」。目前，開發者被迫在高度主觀的框架（如 LangChain 或 LlamaIndex，容易造成架構鎖定）或是缺乏標準化記憶、工具與工作流機制的原生 API 之間做選擇。

**Portable Agent Protocol (PAP)** 填補了這個空白。PAP 是一個「AI 原生工作區協定」，透過標準化的 `.agent/` 目錄結構來儲存 Agent 的狀態、工具與知識。其核心設計哲學為「**文件即協定 (Documentation as Protocol)**」——使用人類可讀的 Markdown 作為主要介面。這確保了人類與 AI 都能無縫地讀取、理解並修改 Agent 的工作區，打造出真正可攜且不受框架限制的協作環境。

---

## 2. The Problem: Framework Lock-in vs. API Fragmentation / 當前痛點：框架鎖定與 API 碎片化

When building multi-agent systems, teams face two extreme approaches:
1. **Heavy Frameworks (LangChain, LlamaIndex, AutoGen):** Excellent for quick prototyping but introduce steep learning curves, rapid deprecation cycles, and rigid, hard-to-debug abstractions.
2. **Raw Model APIs (OpenAI, Vendor LLMs):** Maximum flexibility, but zero built-in persistence. Developers must reinvent how agents remember past conversations, discover tools, and execute multi-step workflows.

**The Result:** A lack of "Workspace Portability". An agent built in Python using Framework A cannot easily share its prompts, tools, or memory with a TypeScript agent using Framework B.

當建構多智能體系統時，團隊通常面臨兩種極端：
1. **重度框架（LangChain, LlamaIndex, AutoGen）：** 適合快速建立原型，但學習曲線陡峭、棄用週期短，且其抽象層往往僵化且難以除錯。
2. **原生模型 API（OpenAI, Vendor LLMs）：** 提供最大彈性，但完全沒有內建持久化機制。開發者必須重新發明輪子來處理 Agent 的記憶、工具發現與多步驟工作流。

**結果：** 缺乏「工作區可攜性 (Workspace Portability)」。用 Python 搭配 A 框架寫的 Agent，無法輕易地將它的提示詞、工具或記憶，分享給用 TypeScript 搭配 B 框架寫的 Agent。

---

## 3. The Philosophy: Documentation as Protocol / 核心哲學：文件即協定

To solve portability, PAP introduces a paradigm shift: **Documentation as Protocol**.

Instead of complex JSON payloads or rigid database schemas, PAP stores the agent's contract in `.agent/*.md` files. 
- **For Humans:** It reads like standard project documentation. You can open `.agent/agent.md` or `.agent/skills.md` in any text editor and instantly understand what the agent does.
- **For AI:** Large Language Models naturally excel at reading and parsing Markdown. By feeding these files directly into the LLM's context window, the AI instantly grasps its persona, available tools, and workflow definitions without complex deserialization.

為了解決可攜性問題，PAP 帶來了典範轉移：「**文件即協定**」。

PAP 不依賴複雜的 JSON 負載或僵硬的資料庫 Schema，而是將 Agent 的合約儲存在 `.agent/*.md` 檔案中。
- **對人類而言：** 這些檔案就像標準的專案文件，用任何編輯器打開 `.agent/agent.md` 就能立刻了解 Agent 的功能。
- **對 AI 而言：** 大型語言模型天生擅長閱讀與解析 Markdown。將這些檔案直接丟進 LLM 的 Context 中，AI 就能瞬間理解其角色、可用工具與工作流定義，完全不需要複雜的反序列化過程。

---

## 4. Ecosystem Positioning: PAP, MCP, and A2A / 生態系定位

PAP is designed to complement, not compete with, emerging standards:

- **vs. MCP (Model Context Protocol):** MCP defines a standard JSON-RPC protocol for connecting an AI to external tools and data sources. **PAP integrates with MCP**. PAP acts as the project-level orchestrator (the "brain" and "workspace") that can sync and consume MCP tools (the "hands"), translating MCP JSON Schemas into readable `.agent/skills/*.md` contracts.
- **vs. Google A2A (Agent-to-Agent):** A2A focuses on how agents communicate messages over the wire. PAP focuses on the shared local workspace and memory contract.

PAP 的設計理念是與新興標準「互補」，而非競爭：

- **對比 MCP：** MCP 定義了 AI 連接外部工具的 JSON-RPC 協定標準。**PAP 無縫整合 MCP**。PAP 作為專案級別的協調者（大腦與工作區），負責同步並消耗 MCP Server 的工具（手腳），將 MCP 的 Schema 轉譯成可讀的 `.agent/skills/*.md` 檔案。
- **對比 Google A2A：** A2A 專注於 Agent 之間的即時訊息通訊協定，而 PAP 則專注於共享的本地工作區與持久化記憶合約。

---

## 5. Strategic Roadmap / 戰略藍圖

To cement PAP as a community standard, we are executing a three-phase roadmap:
1. **Phase 1: Maturation (Completed)** - Implementation of rigorous Semantic Versioning (`protocol_version`), CLI Validators, and Pluggable Memory Backends (SQLite, JSON).
2. **Phase 2: Ecosystem Building** - Introducing DAG-based Executable Workflows and cross-language runtimes (TypeScript/JS) to capture the broader web ecosystem.
3. **Phase 3: Standardization & Hub** - Launching the `.agent/ Hub`, a public registry where developers can share, fork, and rate Agent profiles, forming a powerful network effect analogous to Docker Hub.

為確立 PAP 的社群標準地位，我們正在執行三階段戰略：
1. **第一階段：協定成熟化（已完成）** - 實作嚴格的語義版本控制 (`protocol_version`)、CLI 驗證器，以及可插拔的記憶體後端（SQLite, JSON）。
2. **第二階段：生態建設** - 引入基於 DAG 的可執行工作流引擎，並開發跨語言 Runtime（TypeScript/JS），以觸及更廣大的 Web 開發社群。
3. **第三階段：標準化與共享平台** - 推出 `.agent/ Hub`，讓開發者能公開分享、分支 (fork) 並評價 Agent 配置，打造類似 Docker Hub 的強大網路效應護城河。

---

**Join the Movement:** By adopting the `.agent/` directory, you are future-proofing your AI projects against framework lock-in. Build with PAP today.
**加入我們：** 採用 `.agent/` 目錄，讓您的 AI 專案免於框架鎖定的風險。現在就開始使用 PAP 吧！
