#!/usr/bin/env python3
"""Example demonstrating Cross-Agent State Handoff (Phase 1-04).

This script simulates a scenario where a 'Planner Agent' works on a task,
populates its memory with intermediate results, and then exports a handoff packet.
A 'Worker Agent' then imports the handoff packet to resume execution.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from agent_runtime.engine import AgentEngine

# Sample configuration for the agents
AGENT_A_CONFIG = """\
---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: planner-agent
version: "1.0.0"
purpose: Plan tasks and coordinate actions.
language: en-US
authorization_level: interactive-approval
use_case_tags: [planning]
tools: []
protocol:
  root: .agent/
  manifest: .agent/agent.md
  directories:
    memory: .agent/memory/
memory:
  backend: local
  path: .agent/memory/
---
# Planner Agent Manifest
"""

AGENT_B_CONFIG = """\
---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: coder-agent
version: "1.0.0"
purpose: Write and refactor code.
language: en-US
authorization_level: interactive-approval
use_case_tags: [coding]
tools: []
protocol:
  root: .agent/
  manifest: .agent/agent.md
  directories:
    memory: .agent/memory/
memory:
  backend: local
  path: .agent/memory/
---
# Coder Agent Manifest
"""


def main() -> None:
    print("=== Portable Agent Protocol (PAP) Cross-Agent Handoff Demo ===")

    # Use a temporary directory as the simulation workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"Creating isolated simulation workspace: {workspace.resolve()}\n")

        # 1. Setup Planner Agent (Agent A)
        dir_a = workspace / "planner_agent"
        dir_a_agent = dir_a / ".agent"
        dir_a_mem = dir_a_agent / "memory"
        dir_a_mem.mkdir(parents=True)
        (dir_a_agent / "agent.md").write_text(AGENT_A_CONFIG, encoding="utf-8")

        # Copy spec memory schema to allow validation
        spec_dir_a = dir_a / "spec"
        spec_dir_a.mkdir(parents=True)
        real_schema = Path("spec/memory.schema.json")
        if real_schema.exists():
            shutil.copy2(real_schema, spec_dir_a / "memory.schema.json")

        print("[Planner Agent] Initializing...")
        planner = AgentEngine(config_path=dir_a_agent / "agent.md")

        # Simulate Planner Agent finding some intermediate results and storing them in memory
        print("[Planner Agent] Populating memory with plan detail and code structure...")
        planner.memory.write("target_module", "agent_runtime.prompt_composer")
        planner.memory.write(
            "refactoring_steps",
            [
                "Define prompt.schema.json",
                "Implement PromptComposer loader",
                "Add prompt injection protection patterns",
            ],
        )
        planner.memory.write("status_report", {"progress": "33%", "current_step": 1})

        # 2. Export Handoff from Planner Agent
        print("\n[Planner Agent] Exporting handoff packet...")
        handoff_id = planner.export_handoff(
            task_state="Phase 1-03 Prompt Registry initial layout design completed.",
            pending_steps=[
                "Implement PromptComposer",
                "Integrate with AgentEngine",
                "Run test suites and verify robustness",
            ],
            context_summary=(
                "We need to implement prompt parsing, injection protection, and schema validation. "
                "I have identified the target module and initial steps. Over to you for the implementation."
            ),
            memory_keys=["target_module", "refactoring_steps", "status_report"],
            handoff_id="handoff-plan-to-code",
        )
        print(f"Exported Handoff ID: {handoff_id}")

        src_handoff_file = dir_a_mem / "handoff" / f"{handoff_id}.json"
        print(f"Handoff packet written to: {src_handoff_file.relative_to(workspace)}")

        # Print the handoff packet details
        with src_handoff_file.open(encoding="utf-8") as f:
            packet_data = json.load(f)
        print(f"Checksum: {packet_data['checksum']}")

        # 3. Setup Coder Agent (Agent B) in a distinct workspace directory
        dir_b = workspace / "coder_agent"
        dir_b_agent = dir_b / ".agent"
        dir_b_mem = dir_b_agent / "memory"
        dir_b_mem.mkdir(parents=True)
        (dir_b_agent / "agent.md").write_text(AGENT_B_CONFIG, encoding="utf-8")

        # Copy spec memory schema to allow validation
        spec_dir_b = dir_b / "spec"
        spec_dir_b.mkdir(parents=True)
        if real_schema.exists():
            shutil.copy2(real_schema, spec_dir_b / "memory.schema.json")

        print("\n[Coder Agent] Initializing...")
        coder = AgentEngine(config_path=dir_b_agent / "agent.md")

        # Verify Coder Agent has empty memory initially
        print(f"[Coder Agent] Memory key 'target_module': {coder.memory.read('target_module')}")

        # 4. Simulate Handoff Transfer
        print("\n[System] Simulating physical transmission of handoff packet...")
        dest_handoff_dir = dir_b_mem / "handoff"
        dest_handoff_dir.mkdir(parents=True, exist_ok=True)
        dest_handoff_file = dest_handoff_dir / f"{handoff_id}.json"
        shutil.copy2(src_handoff_file, dest_handoff_file)
        print(f"Packet received at: {dest_handoff_file.relative_to(workspace)}")

        # 5. Coder Agent Imports Handoff
        print("\n[Coder Agent] Importing handoff packet and restoring state...")
        imported = coder.import_handoff(handoff_id)

        print("\n=== Imported Metadata ===")
        print(f"Task State      : {imported['task_state']}")
        print(f"Pending Steps   : {imported['pending_steps']}")
        print(f"Context Summary : {imported['context_summary']}")

        # 6. Verify Restored Memory in Coder Agent
        print("\n=== Restored Memory in Coder Agent ===")
        print(f"target_module     : {coder.memory.read('target_module')}")
        print(f"refactoring_steps : {coder.memory.read('refactoring_steps')}")
        print(f"status_report     : {coder.memory.read('status_report')}")

        print("\n[Success] State migration completed cleanly without loss of context!")


if __name__ == "__main__":
    main()
