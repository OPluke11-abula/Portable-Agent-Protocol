"""Example 00: PAP Quickstart (5-minute guide).

This script demonstrates how to initialize, validate, load, and inspect
a Portable Agent Protocol workspace.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

# Add project root to python path to run without installation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import scaffold_workspace
from agent_runtime.engine import load_agent_config, validate_agent_workspace, AgentEngine


def main() -> None:
    # 1. Create a temporary directory for the workspace
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        print(f"Creating a temporary workspace at: {tmp_path}")

        # 2. Scaffold workspace using cli helper
        scaffold_workspace(
            base_dir=tmp_path,
            project_name="quickstart-project",
            agent_name="QuickstartAgent",
            skills_list=["search_web", "query_db"],
            dry_run=False
        )

        config_path = tmp_path / ".agent" / "agent.md"
        assert config_path.exists(), "Scaffolding failed."

        # Copy over spec schemas to make sure validation works
        spec_dir = tmp_path / "spec"
        spec_dir.mkdir(exist_ok=True)
        original_root = Path(__file__).parent.parent
        for schema_file in original_root.glob("spec/*.json"):
            shutil.copy(schema_file, spec_dir / schema_file.name)

        print("\n--- 1. Validating Workspace ---")
        try:
            validate_agent_workspace(config_path)
            print("OK: Workspace validation succeeded!")
        except Exception as e:
            print(f"Error: Workspace validation failed: {e}")
            return

        print("\n--- 2. Loading Config ---")
        config = load_agent_config(config_path)
        print(f"Agent Name: {config.get('name')}")
        print(f"Protocol Version: {config.get('protocol_version')}")
        print(f"Supported Tools: {config.get('tools')}")

        print("\n--- 3. Instantiating Agent Engine ---")
        engine = AgentEngine(config_path)
        print(f"Engine status: READY")
        print(f"Active tools in router: {engine.router.available_tools}")

        print("\nQuickstart finished successfully!")


if __name__ == "__main__":
    main()
