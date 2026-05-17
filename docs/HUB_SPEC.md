# .agent/ Hub Specification

## 1. Overview
The **`.agent/ Hub`** is the public registry and sharing ecosystem for the Portable Agent Protocol. It allows developers to discover, download, and share pre-configured AI Agent workspaces. 

Instead of starting from scratch, a developer can run:
`pap hub clone username/agent-name`
to instantly provision an agent with its persona, tools, workflows, and knowledge base ready to go.

## 2. Architecture: Git-Backed Registry
To rapidly bootstrap the ecosystem, the `.agent/ Hub` operates as a **Git-backed decentralized registry**.
- The canonical index is a central GitHub repository (the "Hub Registry") containing pointers to individual Agent repositories.
- `pap hub clone` resolves the agent name to a Git URL and performs a sparse checkout of the `.agent/` directory, placing it into the user's local project.

### 2.1 Resolution Flow
1. User types `pap hub clone acme/finance-bot`.
2. CLI queries the Hub Registry (e.g., `https://github.com/PAP-Hub/registry`).
3. CLI finds the repository URL for `acme/finance-bot`.
4. CLI downloads the `.agent/` folder from that repository.

## 3. Packaging & Security (`pap hub pack`)
Security is critical when sharing agent profiles. Developers often have active memory files (`memory.json`) or environment variable files (`.env`) inside their workspace that contain API keys, sensitive chat logs, or PII.

When a developer runs `pap hub pack`, the CLI performs a **safe compression**:
- **Included:** `agent.md`, `persona.md`, `skills/*.md`, `workflows/*.md`, `knowledge/`.
- **Excluded:** `memory/` (all contents), `*.env`, `*.sqlite`, `.git/`, and any runtime logs.

The output is an `.agent-profile.tar.gz` artifact that is safe for public distribution on GitHub Releases or the future Web Registry.

## 4. Future: Centralized Web Registry
Once the Git-backed ecosystem gains critical mass, the Hub will evolve into a full Web API (similar to `npmjs.com` or `hub.docker.com`), providing:
- Rating and review systems.
- Vulnerability scanning on uploaded tool schemas.
- Dependency management (e.g., an agent profile that inherently depends on a specific MCP server version).
