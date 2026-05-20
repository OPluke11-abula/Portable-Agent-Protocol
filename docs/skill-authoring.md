# Skill Authoring Guide: Building Capabilities in PAP

In the Portable Agent Protocol, an agent's capabilities are formally decoupled from the underlying runtime execution through **Skill Contracts**. 

A skill contract specifies the input parameters, data types, constraints, and return schemas of a capability. This formal separation:
1. Gives AI planning systems perfect clarity on what tools are available and how to call them.
2. Ensures complete type safety by validating parameter payloads *before* they are sent to the execution environment.
3. Facilitates cross-platform portability by keeping the description of a capability separate from its programming language implementation.

---

## 1. Structure of a Skill Contract File

Skill contracts are located in `.agent/skills/<skill_id>.md`. They consist of two parts:
1. **YAML Frontmatter**: The official JSON Schema contract defining the inputs, outputs, version, and usage description.
2. **Markdown Body**: Detailed human/model-readable documentation, usage guidelines, safety rules, and operational constraints.

### Core Contract Schema

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `id` | `string` | **Yes** | Unique identifier of the skill (must match filename exactly). |
| `version` | `string` | **Yes** | Semantic version of the skill (e.g. `1.0.0`). |
| `description` | `string` | **Yes** | A clear explanation of what the tool does. Highly critical for LLM tool selection. |
| `inputs` | `object` | **Yes** | JSON Schema describing parameters the skill accepts. |
| `outputs` | `object` | **Yes** | JSON Schema describing the shape of the result returned by the skill. |
| `safety_notes` | `string` | No | Operational bounds, rate limits, or warnings. |

---

## 2. Step-by-Step Walkthrough: Creating a Custom Skill

Let's create a custom capability called `send_notification` that dispatches slack alerts or emails.

### Step 2.1: Write the Contract File (`.agent/skills/send_notification.md`)

Create the markdown file defining your parameters:

```yaml
---
id: "send_notification"
version: "1.0.0"
description: "Send a text-based alert or notification to a specific channel."
inputs:
  type: "object"
  properties:
    channel:
      type: "string"
      enum: ["slack", "email", "sms"]
      description: "Destination notification channel."
    recipient:
      type: "string"
      description: "Email address, channel ID, or phone number."
    message:
      type: "string"
      description: "Detailed message body."
  required:
    - channel
    - recipient
    - message
outputs:
  type: "object"
  properties:
    status:
      type: "string"
      enum: ["success", "failed"]
    timestamp:
      type: "string"
    delivery_id:
      type: "string"
---
# send_notification
Enables sending text notifications across Slack channels, emails, or SMS alerts.
Use this skill whenever audit failures or validation issues occur and need developer awareness.
```

### Step 2.2: Register the Skill in the Registry (`.agent/skills.md`)

Open `.agent/skills.md` and add the new capability ID under the `skills` list:

```yaml
---
schema_version: "1.0.0"
skills:
  - "read_file"
  - "list_dir"
  - "send_notification"
---
# Registered Capabilities Index
```

### Step 2.3: Enable the Skill in the Agent Manifest (`.agent/agent.md`)

To authorize your agent to use this skill, register it in `.agent/agent.md` under the `tools` array:

```yaml
---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: "alert-agent"
version: "0.1.0"
purpose: "Monitor log files and alert developers of issues."
language: "en-US"
authorization_level: "interactive-approval"
use_case_tags:
  - "ops"
tools:
  - "read_file"
  - "send_notification"
# ... rest of file ...
```

---

## 3. Implementing the Tool Handler in Python

In the reference Python runtime, execution dispatching is handled by registering callable hooks inside the engine's router.

Here is how you write and hook the execution logic for the `send_notification` skill:

```python
import datetime
import uuid
from agent_runtime.engine import AgentEngine

# 1. Instantiate the PAP Agent Engine
engine = AgentEngine(".agent/agent.md")

# 2. Define the execution function
def handle_send_notification(params: dict) -> dict:
    channel = params["channel"]
    recipient = params["recipient"]
    message = params["message"]
    
    # Execute the actual delivery logic
    print(f"[ACTION] Delivering message to {recipient} via {channel}: {message}")
    
    # Return a dictionary matching the 'outputs' schema in your contract
    return {
        "status": "success",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "delivery_id": str(uuid.uuid4())
    }

# 3. Register the handler in the tool router
engine.router.register_handler("send_notification", handle_send_notification)

# 4. Dispatching a validated execution
payload = {
    "channel": "slack",
    "recipient": "#ops-alerts",
    "message": "Staging DB connection timed out!"
}
result = engine.router.dispatch("send_notification", payload)
print(f"Delivered! Status: {result['status']}, ID: {result['delivery_id']}")
```

---

## 4. Linting and Validating Your Skill Contracts

To verify that your newly authored skill contract conforms to the standard PAP specs, run the built-in workspace linter:

```bash
python cli.py lint
```

The linter will perform the following checks:
- **Registry Alignment**: Ensures every skill in `agent.md` exists in `skills.md` and has a matching `.md` contract file under `skills/`.
- **Contract Schema Syntax**: Validates that the YAML frontmatter in your contract conforms exactly to the formal `spec/skill-contract.schema.json` specification.
- **Auto-Fixing**: Run `python cli.py lint --fix` to automatically repair minor formatting inconsistencies.
