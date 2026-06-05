# Getting Started with Portable Agent Protocol (PAP)

Welcome to the **Portable Agent Protocol (PAP)**! PAP is a standard specification and runtime interface for building portable, secure, and vendor-agnostic AI agent environments. 

By separating agent identity, memory, capabilities, and workflows into standard, readable Markdown manifests and JSON Schemas, PAP allows agents to transition seamlessly across different runtimes, hosts, and AI systems without lock-in.

---

## 1. Prerequisites

To run the PAP reference implementation, you will need:
- **Python 3.10** or higher (tested up to Python 3.14)
- **pip** (Python package installer)

---

## 2. Installation

Clone the repository and install the library in editable mode along with its core dependencies:

```bash
git clone https://github.com/OPluke11-abula/Portable-Agent-Protocol.git
cd Portable-Agent-Protocol
pip install -e .
```

Alternatively, install the core dependencies directly:
```bash
pip install jsonschema pyyaml
```

---

## 3. Initializing a Workspace

The PAP CLI provides a helper subcommand to scaffold a brand-new, standard-compliant agent workspace in any directory.

### CLI Usage

```bash
python cli.py init [OPTIONS]
```

### Options
* `--project-name TEXT`: Name of the parent project.
* `--agent-name TEXT`: Name of the agent.
* `--skills TEXT`: Comma-separated list of initial skills/tools to scaffold.
* `--dry-run`: Simulate directory and file generation without writing them to disk.

### Interactive Scaffolding

If you run `python cli.py init` without options, the CLI will guide you through an interactive setup:

```text
> python cli.py init
Project Name [my-agent-project]: billing-assistant
Agent Name [BillingAgent]: BillBot
Skills list (comma-separated, e.g. search_web, query_db): query_invoices, send_receipt
...
PAP workspace scaffolded successfully!
```

---

## 4. Understanding the Workspace Layout

The CLI creates a hidden `.agent/` directory containing the modular manifests:

```text
my-project/
├── .agent/
│   ├── agent.md            # Primary agent metadata config
│   ├── skills.md           # Registered capabilities index
│   ├── prompts.md          # Entrypoint catalog for prompt templates
│   ├── memory.md           # Memory persistence declaration
│   ├── workflows.md        # Declared multi-step DAG workflows
│   ├── persona_template.md # Base prompt for the agent's identity
│   ├── skills/
│   │   ├── _template.md    # Reusable capability template
│   │   ├── query_invoices.md
│   │   └── send_receipt.md
│   ├── prompts/            # Directory for dedicated prompt files
│   ├── memory/             # Local memory persistent storage (JSON/JSONL)
│   └── knowledge_base/     # Markdown files containing domain knowledge
└── spec/                   # Copied schemas for offline validation
```

---

## 5. Bootstrapping the Agent Engine

With your workspace scaffolded, you can bootstrap the runtime engine in just a few lines of Python:

```python
from pathlib import Path
from agent_runtime.engine import AgentEngine

# Path to the primary agent manifest
config_path = Path(".agent/agent.md")

# Load and bootstrap the agent runtime
engine = AgentEngine(config_path)

print(f"Agent Engine Loaded!")
print(f"Agent Name: {engine.name}")
print(f"Protocol Version: {engine.version}")
print(f"Active capabilities in router: {engine.router.available_tools}")
```

---

## 6. Performing Your First Skill Call

PAP enforces strict input/output validation against your skill contracts before a tool is executed.

Here is how to dispatch a validated skill call through the router:

```python
# 1. Prepare valid parameter inputs
valid_params = {
    "invoice_id": "INV-2026-004",
    "include_audit": True
}

# 2. Run dry-run validation (optional)
engine.router.validate_call("query_invoices", valid_params)

# 3. Dispatch the call to get results
result = engine.router.dispatch("query_invoices", valid_params)
print("Skill Call Completed successfully:")
print(result)
```

### Under the Hood: Schema Enforcement

If you pass invalid parameters (e.g. missing a required field or of a wrong data type):

```python
invalid_params = {
    "invoice_id": 12345,  # Needs to be a string
}

try:
    engine.router.dispatch("query_invoices", invalid_params)
except ValueError as e:
    print(f"Blocked call: {e}")
    # Output: Blocked call: Validation failed for skill 'query_invoices': ...
```

---

## 7. Next Steps

Now that you have your first workspace up and running, explore the rest of the guides to deepen your integration:

* **[Protocol Specification](protocol-spec.md)**: Deep dive into `.agent/` folder conventions and manifest schemas.
* **[Skill Authoring Guide](skill-authoring.md)**: Learn how to declare custom capability contracts and implement backend tool handlers.
* **[Memory Management Guide](memory-guide.md)**: Master episodic memory, semantic facts, and state persistence.
* **[Workflow Guide](workflow-guide.md)**: Create multi-step, directed acyclic graph (DAG) tasks for your agents.
* **[Multi-Agent Cooperation & Handoffs](multi-agent.md)**: Securely transfer tasks between different agents with cryptographic checksum integrity.
