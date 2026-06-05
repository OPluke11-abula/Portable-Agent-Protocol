# Tech Talk Pitch & Outline / 社群演講提案與大綱

This document contains ready-to-use speaker pitches and slide outlines for submitting the Portable Agent Protocol (PAP) to developer conferences (e.g., PyCon Taiwan, COSCUP, Local AI Meetups).

本文件提供現成的演講提案與投影片大綱，方便將 PAP 投稿至各大開發者年會（如 PyCon Taiwan, COSCUP, AI Meetup 社群）。

---

## 1. Talk Title Proposals / 演講標題提案

- **Option A:** Beyond Frameworks: Building AI-Native Workspaces with the Portable Agent Protocol
- **Option B:** Documentation as Protocol: The Future of Agentic Collaboration
- **選項 A (中文):** 跨越框架鎖定：使用 Portable Agent Protocol 打造 AI 原生工作區
- **選項 B (中文):** 文件即協定：探索 AI 智能體協作的下一步與 .agent/ 的奧秘

## 2. Target Audience / 目標受眾
- **Primary:** AI Developers, System Architects, LLM Application Builders, DevOps Engineers.
- **Prerequisites:** Basic understanding of LLMs, prompts, and tool-calling (function calling).

## 3. Abstract (For CFP Submission) / 演講摘要（投稿用）

**English:**
The AI Agent ecosystem is suffering from extreme fragmentation. Developers are stuck choosing between rigid frameworks (LangChain, LlamaIndex) that cause vendor lock-in, or raw APIs that lack persistence for memory, tools, and workflows. 

Enter the **Portable Agent Protocol (PAP)**. In this talk, we introduce an "AI-Native Workspace Protocol" that standardizes agent configurations using a `.agent/` directory. By adopting a "Documentation as Protocol" philosophy, PAP uses human-readable Markdown as the primary interface—allowing both humans and AI to seamlessly read, understand, and modify the workspace. We will demonstrate how PAP avoids framework lock-in, integrates smoothly with the Model Context Protocol (MCP), and provides a fully pluggable memory and tool routing architecture in Python. Join us to learn how to future-proof your multi-agent systems!

**繁體中文:**
目前的 AI Agent 生態系正面臨嚴重的碎片化問題。開發者被迫在「容易造成架構鎖定」的重度框架（如 LangChain, LlamaIndex），與「缺乏持久化記憶、工具及工作流機制」的原生 API 之間做選擇。

本次演講將介紹 **Portable Agent Protocol (PAP)**——一個全新的「AI 原生工作區協定」。PAP 透過標準化的 `.agent/` 目錄結構來管理 Agent 狀態，並首創「文件即協定 (Documentation as Protocol)」的設計哲學。我們使用人類可讀的 Markdown 作為主要介面，讓開發者與 AI 都能零障礙地讀取並修改工作區。我將現場展示 PAP 如何打破框架鎖定、無縫橋接 MCP (Model Context Protocol) 生態，並展示其在 Python 中強大的可插拔記憶體與工具路由架構。歡迎加入我們，一起探索多智能體系統的未來！

---

## 4. Slide Deck Structure (30-Minute Format) / 投影片大綱（30 分鐘版）

### 0-5 mins: The Chaos of Agent Frameworks / 破冰：Agent 框架的亂象
- **Slide 1:** The explosion of AI Frameworks in 2024-2025.
- **Slide 2:** The "Lock-in" Problem: Why migrating a LangChain agent to LlamaIndex is a nightmare.
- **Slide 3:** The Missing Piece: The Protocol Layer.

### 5-15 mins: Introducing PAP & "Documentation as Protocol" / 介紹 PAP 與「文件即協定」
- **Slide 4:** What is the `.agent/` directory? (The AI Workspace).
- **Slide 5:** Why Markdown? (LLMs read Markdown better than deep JSON schemas).
- **Slide 6:** Live Demo: Initializing a PAP workspace (`python cli.py init` and VS Code Extension IntelliSense).

### 15-25 mins: Architecture Deep Dive & Ecosystem / 架構深潛與生態系
- **Slide 7:** The Three-Layer Layout: Manifest -> Registries -> Detailed Context.
- **Slide 8:** Pluggable Memory Backends (In-memory, JSON, SQLite).
- **Slide 9:** Bridging the Gap: PAP + MCP (Model Context Protocol). How PAP orchestrates MCP tools dynamically.

### 25-30 mins: Roadmap and Call to Action / 藍圖與行動呼籲
- **Slide 10:** The Future: Executable DAG Workflows and `.agent/ Hub`.
- **Slide 11:** How to contribute (We need TypeScript developers!).
- **Slide 12:** Q&A.
