"""Executable sample demonstrating stateful WorkflowEngine execution, checkpointing, and resumption.

This script scaffolds a temporary agent workspace, registers tools, runs a multi-step workflow
that initially fails, inspects the persisted checkpoint in the memory backend, fixes the trigger,
and resumes execution seamlessly from the failed step.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import textwrap
from pathlib import Path

from agent_runtime.engine import AgentEngine
from agent_runtime.workflow_engine import WorkflowEngine


def run_sample() -> None:
    # 1. Setup a temporary agent workspace
    temp_dir = Path(tempfile.mkdtemp(prefix="pap_workflow_sample_"))
    print(f"=== 1. Scaffolding temporary workspace at: {temp_dir} ===")

    agent_dir = temp_dir / ".agent"
    workflows_dir = agent_dir / "workflows"
    skills_dir = agent_dir / "skills"
    memory_dir = agent_dir / "memory"

    workflows_dir.mkdir(parents=True)
    skills_dir.mkdir()
    memory_dir.mkdir()

    # Create dummy skill spec files
    (skills_dir / "data_fetcher.md").write_text("# data_fetcher\n", encoding="utf-8")
    (skills_dir / "data_processor.md").write_text("# data_processor\n", encoding="utf-8")

    # Create the sample workflow with a 3-step DAG:
    # step_1 (fetch) -> step_2 (process, fails initially) -> step_3 (respond)
    workflow_content = textwrap.dedent(
        """\
        ---
        name: sample_pipeline
        steps:
          - id: fetch_data
            tool: data_fetcher
            params:
              source: "{{ inputs.source_url }}"
          - id: process_data
            tool: data_processor
            depends_on: [fetch_data]
            params:
              raw_content: "{{ fetch_data.output.data }}"
              mode: "strict"
          - id: finalize_response
            action: respond
            depends_on: [process_data]
            params:
              final_result: "{{ process_data.output.processed }}"
              status: "completed"
        ---
        # Sample Pipeline Workflow
        """
    )
    (workflows_dir / "sample_pipeline.md").write_text(workflow_content, encoding="utf-8")

    # Create agent configuration
    agent_config = textwrap.dedent(
        f"""\
        ---
        protocol_version: "1.0.0"
        min_runtime_version: "0.1.0"
        name: sample-workflow-agent
        version: "0.1.0"
        purpose: Demonstrate PAP workflow state machine and resumption.
        language: en-US
        authorization_level: interactive-approval
        use_case_tags: [sample]
        tools:
          - data_fetcher
          - data_processor
        protocol:
          root: .agent/
          manifest: .agent/agent.md
          directories:
            skills: .agent/skills/
            workflows: .agent/workflows/
        memory:
          backend: local
          path: {memory_dir.as_posix()}
        ---
        # Sample Workflow Agent
        """
    )
    (agent_dir / "agent.md").write_text(agent_config, encoding="utf-8")

    # 2. Bootstrap Agent Engine
    print("\n=== 2. Bootstrapping Agent Engine ===")
    engine = AgentEngine(config_path=agent_dir / "agent.md")

    # Register mock tools
    def mock_fetcher(params):
        print(f"  [Tool: data_fetcher] Fetching from source: {params['source']}")
        return {"data": "RAW_JSON_DATA_FROM_WEB"}

    should_fail = True
    def mock_processor(params):
        nonlocal should_fail
        print(f"  [Tool: data_processor] Processing: {params['raw_content']}")
        if should_fail:
            print("  [Tool: data_processor] ERROR: Simulating a data format exception!")
            raise ValueError("Invalid format: expected CSV, got JSON")
        print("  [Tool: data_processor] Processing successful!")
        return {"processed": f"PROCESSED_({params['raw_content']})"}

    engine.router.register_tool("data_fetcher", mock_fetcher)
    engine.router.register_tool("data_processor", mock_processor)

    # 3. Execute Workflow (First attempt: will fail at step 2)
    print("\n=== 3. Executing Workflow (Attempt 1: Expecting Failure) ===")
    wf_engine = WorkflowEngine(engine)

    session_id = None
    try:
        wf_engine.run("sample_pipeline", {"source_url": "https://example.com/api"})
    except Exception as e:
        print(f"\n>>> Workflow Execution Halted: {e}")

    # 4. Inspect persisted checkpoint state from memory
    print("\n=== 4. Inspecting Memory Checkpoint State ===")
    session_keys = [k for k in engine.memory.list_keys() if k.startswith("workflow:sample_pipeline:session:")]
    if session_keys:
        session_key = session_keys[0]
        session_id = session_key.split(":")[-1]
        session_data = engine.memory.read(session_key)

        print(f"Session ID: {session_id}")
        print(f"Session Status: {session_data['status']}")
        print("Step States:")
        for step_id, state in session_data["step_states"].items():
            err_info = f" (Error: {state['error']})" if "error" in state else ""
            print(f"  - {step_id}: {state['status']}{err_info}")
        
        # Verify downstream skipped steps
        assert session_data["step_states"]["finalize_response"]["status"] == "skipped"

        # Check the persistence of the failure logs in memory
        err_log = engine.memory.read(f"workflow_error:sample_pipeline:process_data")
        print("\nFailure Log persisted in memory:")
        print(f"  Error message: {err_log['error']}")
    else:
        print("Error: No session checkpoint found in memory!")
        return

    # 5. Resume execution from checkpoint
    print("\n=== 5. Fixing Trigger & Resuming Workflow from Checkpoint ===")
    # Fix the issue so processor now succeeds
    should_fail = False

    # Execute resumption
    print(f"Resuming workflow session '{session_id}'...")
    final_result = engine.resume_workflow("sample_pipeline", session_id)

    print("\n=== 6. Workflow Completed Successfully ===")
    print("Final Output Context:")
    for step_id, out in final_result.items():
        if step_id != "inputs":
            print(f"  - {step_id}: {out}")

    # Verify memory states are updated to success
    final_session_data = engine.memory.read(session_key)
    print(f"\nFinal Session Status in Memory: {final_session_data['status']}")
    print("Final Step States in Memory:")
    for step_id, state in final_session_data["step_states"].items():
        print(f"  - {step_id}: {state['status']}")

    # Clean up workspace
    shutil.rmtree(temp_dir)
    print(f"\n=== Cleanup complete. Temporary workspace removed ===")


if __name__ == "__main__":
    run_sample()
