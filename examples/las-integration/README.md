# LAS + PAP Integration Example

This directory demonstrates how to integrate the **Portable Agent Protocol (PAP)** with the **Lightweight Agent System (LAS)**.

By combining LAS and PAP, you get the best of both worlds:
- **LAS** provides the lightweight, concurrent agent execution runtime and message bus.
- **PAP** provides the standardized, portable workspace definition (`.agent/`) containing the agent's persona, memory, tools, and workflows.

## Directory Structure

- `.agent/` : A standard PAP workspace tailored for the LAS agent.
- `las_agent.py` : A demonstration script showing how to instantiate a LAS Agent and inject the PAP `AgentEngine` as its configuration and tool routing backbone.

## How it works

1. The `AgentEngine` reads the `.agent/agent.md` manifest and layout.
2. The `LAS Agent` is initialized using the `persona` and `name` loaded by PAP.
3. When the `LAS Agent` needs to invoke a tool, it routes the call through `engine.run(tool, params)`.
4. When the `LAS Agent` needs to persist context, it writes to `engine.memory`.
