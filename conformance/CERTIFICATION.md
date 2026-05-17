# PAP-Compatible Certification

The **Portable Agent Protocol (PAP)** aims to prevent framework lock-in by standardizing the AI agent workspace. To build trust within the ecosystem, we offer a self-certified **"PAP-Compatible"** designation.

Any framework, runtime, or AI application that adheres to the PAP contract can display the official badge on their repository or website.

## The Badge

[![PAP Compatible](https://img.shields.io/badge/PAP--Compatible-blue.svg)](https://github.com/OPluke11-abula/Portable-Agent-Protocol)

**Markdown Snippet:**
```markdown
[![PAP Compatible](https://img.shields.io/badge/PAP--Compatible-blue.svg)](https://github.com/OPluke11-abula/Portable-Agent-Protocol)
```

## Certification Criteria

To display the badge, a project must meet the following three requirements:

1. **Schema Compliance:** The runtime must be able to read `.agent/agent.md` and successfully parse its YAML front matter according to the official `schemas/agent-schema.json`. It must respect `protocol_version`.
2. **Layout Resolution:** The runtime must correctly locate and utilize the required sub-files defined in the `layout` section (e.g., `persona.md`, `memory.md`, `skills/`).
3. **Conformance Testing:** The runtime must implement a test runner that executes and passes all test cases defined in the `conformance/` directory of this repository.

## Officially Certified Frameworks

We proudly recognize the following frameworks that have achieved PAP compatibility:

- 🏅 **[Lightweight Agent System (LAS)](#)** - The first framework to natively adopt PAP for defining agent configurations and memory persistence. (See `examples/las-integration/` for the official implementation guide).
