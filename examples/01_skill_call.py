"""Example 01: PAP Skill Call.

This script demonstrates how to load a skill, trigger validation of the
input parameter schemas, and call the skill using the AgentEngine.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

# Add project root to python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import scaffold_workspace
from agent_runtime.engine import AgentEngine


def main() -> None:
    # 1. Setup workspace
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        print(f"Creating a temporary workspace at: {tmp_path}")

        scaffold_workspace(
            base_dir=tmp_path,
            project_name="skill-project",
            agent_name="SkillAgent",
            skills_list=["search_web"],
            dry_run=False
        )

        config_path = tmp_path / ".agent" / "agent.md"

        # Copy spec files for schema validation
        spec_dir = tmp_path / "spec"
        spec_dir.mkdir(exist_ok=True)
        original_root = Path(__file__).parent.parent
        for schema_file in original_root.glob("spec/*.json"):
            shutil.copy(schema_file, spec_dir / schema_file.name)

        # 2. Instantiate Agent Engine
        engine = AgentEngine(config_path)
        print("AgentEngine initialized.")

        # 3. Successful skill call
        print("\n--- 1. Executing Valid Skill Call ---")
        params = {"query": "python programming", "limit": 3}
        print(f"Params passed: {params}")
        result = engine.run("search_web", params)
        print("Result from search_web:")
        for idx, item in enumerate(result.get("results", [])):
            print(f"  [{idx+1}] {item.get('title')} ({item.get('url')})")
            print(f"      Snippet: {item.get('snippet')}")

        # 4. Failed skill call (validation failure)
        print("\n--- 2. Triggering Schema Validation Error ---")
        bad_params = {"limit": "not-a-number"}  # 'query' is required, 'limit' should be integer
        print(f"Passing bad params: {bad_params}")
        try:
            engine.run("search_web", bad_params)
            print("Error: The call unexpectedly succeeded!")
        except Exception as e:
            print(f"Success: Parameter validation failed as expected: {e}")

        print("\nSkill call example finished successfully!")


if __name__ == "__main__":
    main()
