"""Example 05: PAP Multi-Agent Task Handoff.

This script demonstrates task handoff between two agents:
1. Agent A completes a task, saves progress, and exports state with integrity checksums.
2. The handoff packet is transferred to Agent B's workspace.
3. Agent B imports state, validates checksum integrity, and resumes the task.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

# Add project root to python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import scaffold_workspace
from agent_runtime.engine import AgentEngine


def main() -> None:
    # 1. Setup temporary workspace
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        print(f"Creating a temporary workspace directory at: {tmp_path}")

        # Path to spec schemas for validation
        original_root = Path(__file__).parent.parent

        # -------------------------------------------------------------
        # 1. Setup Source Agent A
        # -------------------------------------------------------------
        print("\n=== Setting up Agent A ===")
        dir_a = tmp_path / "agent_a"
        scaffold_workspace(
            base_dir=dir_a,
            project_name="handoff-project",
            agent_name="AgentA",
            skills_list=[],
            dry_run=False
        )
        config_a = dir_a / ".agent" / "agent.md"

        # Copy spec schemas for Agent A
        spec_dir_a = dir_a / "spec"
        spec_dir_a.mkdir(exist_ok=True)
        for schema_file in original_root.glob("spec/*.json"):
            shutil.copy(schema_file, spec_dir_a / schema_file.name)

        # Inject memory path
        content_a = config_a.read_text(encoding="utf-8")
        escaped_path_a = str(dir_a / ".agent" / "memory").replace("\\", "/") + "/"
        content_a = content_a.replace(
            'backend: "local"\n  path: ".agent/memory/"',
            f'backend: "local"\n  path: "{escaped_path_a}"'
        )
        config_a.write_text(content_a, encoding="utf-8")

        engine_a = AgentEngine(config_a)

        # -------------------------------------------------------------
        # 2. Setup Destination Agent B
        # -------------------------------------------------------------
        print("\n=== Setting up Agent B ===")
        dir_b = tmp_path / "agent_b"
        scaffold_workspace(
            base_dir=dir_b,
            project_name="handoff-project",
            agent_name="AgentB",
            skills_list=[],
            dry_run=False
        )
        config_b = dir_b / ".agent" / "agent.md"

        # Copy spec schemas for Agent B
        spec_dir_b = dir_b / "spec"
        spec_dir_b.mkdir(exist_ok=True)
        for schema_file in original_root.glob("spec/*.json"):
            shutil.copy(schema_file, spec_dir_b / schema_file.name)

        # Inject memory path
        content_b = config_b.read_text(encoding="utf-8")
        escaped_path_b = str(dir_b / ".agent" / "memory").replace("\\", "/") + "/"
        content_b = content_b.replace(
            'backend: "local"\n  path: ".agent/memory/"',
            f'backend: "local"\n  path: "{escaped_path_b}"'
        )
        config_b.write_text(content_b, encoding="utf-8")

        engine_b = AgentEngine(config_b)

        # -------------------------------------------------------------
        # 3. Simulate Agent A Work & Export
        # -------------------------------------------------------------
        print("\n=== 1. Agent A writing key variables to memory ===")
        engine_a.memory.write("target_database", "production_db_v4")
        engine_a.memory.write("completed_milestones", ["schema_setup", "seeding"])
        print("Data persisted in Agent A's memory.")

        print("\n=== 2. Agent A exporting handoff packet ===")
        task_state = "Completed database migration and validation."
        pending_steps = ["Run performance benchmarks", "Generate migration report"]
        context_summary = "All schema migrations successfully applied on staging."

        handoff_id = "migration-handoff-v1"
        exported_id = engine_a.export_handoff(
            task_state=task_state,
            pending_steps=pending_steps,
            context_summary=context_summary,
            memory_keys=["target_database", "completed_milestones"],
            handoff_id=handoff_id
        )
        print(f"Handoff exported successfully! ID: {exported_id}")

        handoff_file_a = dir_a / ".agent" / "memory" / "handoff" / f"{handoff_id}.json"
        assert handoff_file_a.exists(), "Handoff file was not created!"

        # -------------------------------------------------------------
        # 4. Simulate Handoff Transfer
        # -------------------------------------------------------------
        print("\n=== 3. Transferring packet to Agent B ===")
        handoff_file_b = dir_b / ".agent" / "memory" / "handoff" / f"{handoff_id}.json"
        handoff_file_b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(handoff_file_a, handoff_file_b)
        print("Packet successfully transferred.")

        # -------------------------------------------------------------
        # 5. Agent B Import & Validation
        # -------------------------------------------------------------
        print("\n=== 4. Agent B importing handoff packet ===")
        imported = engine_b.import_handoff(handoff_id)
        print("[SUCCESS] Handoff imported and verified successfully!")
        print(f"Imported Task State: {imported['task_state']}")
        print(f"Imported Pending Steps: {imported['pending_steps']}")
        print(f"Imported Context Summary: {imported['context_summary']}")

        print("\n=== 5. Verifying Memory Restoration in Agent B ===")
        db = engine_b.memory.read("target_database")
        milestones = engine_b.memory.read("completed_milestones")
        print(f"Restored target_database: {db}")
        print(f"Restored completed_milestones: {milestones}")

        # -------------------------------------------------------------
        # 6. Checksum Security Verification
        # -------------------------------------------------------------
        print("\n=== 6. Security Check: Testing Checksum Tamper Protection ===")
        # Mangle B's handoff packet file slightly to simulate network corruption/tampering
        packet_data = json.loads(handoff_file_b.read_text(encoding="utf-8"))
        packet_data["task_state"] = "Corrupted/Tampered State"
        handoff_file_b.write_text(json.dumps(packet_data), encoding="utf-8")

        print("Triggering import on tampered packet...")
        try:
            engine_b.import_handoff(handoff_id)
            print("Error: Import of tampered packet unexpectedly succeeded!")
        except ValueError as ve:
            print(f"Success: Handoff import successfully rejected tampered packet: {ve}")

        print("\nMulti-agent handoff example finished successfully!")


if __name__ == "__main__":
    main()
