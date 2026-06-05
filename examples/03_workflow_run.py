"""Example 03: PAP Workflow Run.

This script demonstrates how to configure and run a stateful multi-step
workflow graph with step dependencies, variable interpolation, and action routing.
"""

from __future__ import annotations

import tempfile
import textwrap
from pathlib import Path

# Add project root to python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import scaffold_workspace
from agent_runtime.engine import AgentEngine
from agent_runtime.workflow_engine import WorkflowEngine


def main() -> None:
    # 1. Setup workspace
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        print(f"Creating a temporary workspace at: {tmp_path}")

        scaffold_workspace(
            base_dir=tmp_path,
            project_name="workflow-project",
            agent_name="WorkflowAgent",
            skills_list=[],
            dry_run=False
        )

        config_path = tmp_path / ".agent" / "agent.md"

        # 2. Add custom tool to agent.md
        agent_md_content = config_path.read_text(encoding="utf-8")
        # Add custom_tool to tools list
        agent_md_content = agent_md_content.replace(
            "tools: []",
            "tools:\n  - custom_tool"
        )
        config_path.write_text(agent_md_content, encoding="utf-8")

        # Create skill contract for custom_tool
        contract_path = tmp_path / ".agent" / "skills" / "custom_tool.md"
        contract_content = """---
id: "custom_tool"
name: "Custom Data Processor"
description: "A tool that parses or transforms inputs."
version: "1.0.0"
inputs:
  val:
    type: "string"
    required: true
outputs:
  processed:
    type: "string"
safety_notes: ["Safe to run."]
---
"""
        contract_path.write_text(contract_content, encoding="utf-8")

        # 3. Create a workflow file
        workflow_path = tmp_path / ".agent" / "workflows" / "sample_wf.md"
        workflow_content = """---
name: "sample_wf"
steps:
  - id: step_one
    tool: custom_tool
    params:
      val: "{{ inputs.topic }}"
  - id: step_two
    action: remember
    depends_on: [step_one]
    params:
      key: "saved_topic"
      value: "{{ step_one.output.processed }}"
  - id: step_three
    action: respond
    depends_on: [step_two]
    params:
      msg: "Stored topic successfully"
---
# Sample Workflow
"""
        workflow_path.write_text(workflow_content, encoding="utf-8")

        # 4. Instantiate Agent Engine and register our custom tool handler
        engine = AgentEngine(config_path)
        engine.router.register_tool(
            "custom_tool",
            lambda params: {"processed": f"PROCESSED_VAL_{params['val'].upper()}"}
        )
        print("AgentEngine and custom tool handler initialized.")

        # 5. Run Workflow
        print("\n--- 1. Executing Workflow 'sample_wf' ---")
        wf_engine = WorkflowEngine(engine)
        result = wf_engine.run("sample_wf", {"topic": "antigravity"})

        print("\n--- 2. Checking Workflow Results ---")
        print(f"step_one output: {result['step_one']['output']}")
        print(f"step_two value: {result['step_two']['value']}")
        print(f"step_three response: {result['step_three']['response']}")

        # Verify value saved in memory
        saved_val = engine.memory.read("saved_topic")
        print(f"\n--- 3. Verifying Memory Persistence ---")
        print(f"Value stored in memory for 'saved_topic': {saved_val}")

        print("\nWorkflow run example finished successfully!")


if __name__ == "__main__":
    main()
