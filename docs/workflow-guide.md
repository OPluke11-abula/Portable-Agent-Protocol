# Workflow Design Guide: Structured Task Orchestration in PAP

Complex AI agents often require executing structured, multi-step actions rather than simple single-turn tool dispatches. 

The **Portable Agent Protocol (PAP)** provides a declarative, file-based workflow engine. Workflows are defined in `.agent/workflows.md` as **Directed Acyclic Graphs (DAGs)** of step invocations. 

By defining step sequences, input dependencies, and memory persistence in a structured manifest, runtimes can validate, schedule, and execute complex logic chains with full type safety and automatic parameter interpolation.

---

## 1. Anatomy of a Workflow (`.agent/workflows.md`)

A workflow consists of a unique identifier (e.g. `audit_pipeline`) and a list of steps. Each step executes a registered skill, optionally waiting on dependencies and interpolating results from earlier steps.

### Step Fields

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `tool` | `string` | **Yes** | The skill ID to execute (must have a valid contract in `skills/`). |
| `params` | `object` | No | Inputs to pass to the tool. Supports parameter interpolation using `{step_name.field}`. |
| `depends_on` | `array[string]` | No | List of step IDs that must complete before this step can execute. |
| `persist_to_memory` | `string` | No | Memory variable key where the step's JSON output will be saved. |

---

## 2. Example Workflow Specification

Here is a standard workflows file defining a compliance auditing pipeline:

```yaml
---
schema_version: "1.0.0"
workflows:
  compliance_audit:
    description: "Scan the repository, read corporate policy, and run compliance checks."
    steps:
      scan_files:
        tool: "list_dir"
        params:
          path: "."
      read_policy:
        tool: "read_file"
        params:
          path: "POLICY.md"
          max_lines: 100
        persist_to_memory: "corporate_policy"
      run_check:
        tool: "run_audit"
        depends_on:
          - scan_files
          - read_policy
        params:
          target_files: "{scan_files.files}"
          rule_body: "{read_policy.content}"
          strict_mode: true
        persist_to_memory: "audit_results"
---
# Registered Workflows
```

### Parameter Interpolation Syntax
The workflow engine resolves parameters dynamically before executing each step:
- `{step_name}`: Resolves to the full JSON response returned by the step named `step_name`.
- `{step_name.field}`: Resolves to a specific property in the JSON output. Nested properties are accessed using standard dot notation (e.g., `{step_name.user.email}`).

---

## 3. Running Workflows in Python

The reference Python implementation parses and schedules step execution through `WorkflowEngine`.

Here is how to load the manifest and execute the `compliance_audit` workflow:

```python
from agent_runtime.engine import AgentEngine
from agent_runtime.workflow_engine import WorkflowEngine

# 1. Initialize parent AgentEngine
engine = AgentEngine(".agent/agent.md")

# 2. Register custom tool handlers required by the workflow steps
engine.router.register_handler("list_dir", lambda params: {"files": ["main.py", "utils.py"]})
engine.router.register_handler("read_file", lambda params: {"content": "Rule: No secrets in main.py"})
engine.router.register_handler("run_audit", lambda params: {"violations": 0, "status": "CLEAN"})

# 3. Instantiate WorkflowEngine
workflow_engine = WorkflowEngine(engine)

# 4. Trigger workflow execution
session_id = "audit-session-2026"
result = workflow_engine.run("compliance_audit", session_id)

print(f"\nWorkflow finished! Final states:")
for step_id, step_result in result.items():
    print(f"  Step '{step_id}': status={step_result.get('status')}, output={step_result.get('output')}")
```

---

## 4. Under the Hood: The DAG Execution Cycle

When `WorkflowEngine.run()` is called, the runtime coordinates the following sequence:

1. **Cycle Detection**: Parses dependencies to build a graph. Uses topological sorting to detect cyclic references (e.g. Step A depends on B, B depends on A). If a cycle is detected, execution is aborted with a `ValueError`.
2. **Scheduling**: Places steps into an execution queue sorted by their topological order.
3. **Execution & Interpolation**:
   - For each step, resolves all `{dependency.field}` parameter brackets from the accumulated session context.
   - Validates the interpolated inputs against the skill's formal contract schema.
   - Dispatches the validated tool call.
   - Saves the result to the step context and persists to semantic memory if `persist_to_memory` is defined.

---

## 5. Workflow Design Best Practices

To design clean, reliable agent workflows:

* **Granular, Single-Purpose Steps**: Break down complex actions into small, discrete steps. Instead of a single giant script tool, create separate steps for fetching data, processing parameters, and saving results. This makes debugging much easier and improves tool reuse.
* **Always Declare `depends_on` Explicitly**: If Step B uses interpolated values from Step A (e.g. `{StepA.output_field}`), Step B *must* list `StepA` in its `depends_on` array. This ensures correct topological scheduling.
* **Handle Tool Failure Graces**: Ensure your custom tool handlers return structured errors or empty sets rather than raising unhandled exceptions, allowing subsequent steps to inspect the `status` and handle anomalies safely.
* **Keep Graph Paths Directed & Acyclic**: Ensure that information always flows forward in a clear direction. Avoid loops in your workflow declarations.
