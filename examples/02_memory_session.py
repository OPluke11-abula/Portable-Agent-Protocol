"""Example 02: PAP Memory Session.

This script demonstrates how to persist and retrieve session data using
the persistent memory backend managed by the AgentEngine.
"""

from __future__ import annotations

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
            project_name="memory-project",
            agent_name="MemoryAgent",
            skills_list=[],
            dry_run=False
        )

        config_path = tmp_path / ".agent" / "agent.md"

        # Inject memory path into agent.md so it is fully isolated in temp dir
        agent_md_content = config_path.read_text(encoding="utf-8")
        escaped_path = str(tmp_path / ".agent" / "memory").replace("\\", "/") + "/"
        agent_md_content = agent_md_content.replace(
            'backend: "local"\n  path: ".agent/memory/"',
            f'backend: "local"\n  path: "{escaped_path}"'
        )
        config_path.write_text(agent_md_content, encoding="utf-8")

        # 2. Instantiate Agent Engine
        engine = AgentEngine(config_path)
        print("AgentEngine initialized.")

        # 3. Read/Write values in memory
        print("\n--- 1. Writing to Memory ---")
        engine.memory.write("session_user", {"username": "luke", "role": "admin"})
        engine.memory.write("current_step", 42)
        print("Values successfully written.")

        print("\n--- 2. Reading from Memory ---")
        user = engine.memory.read("session_user")
        step = engine.memory.read("current_step")
        print(f"session_user: {user}")
        print(f"current_step: {step}")

        # 4. Check that memory file actually exists
        memory_file = tmp_path / ".agent" / "memory" / "memory.json"
        print(f"\n--- 3. Verifying File Existence ---")
        if memory_file.exists():
            print(f"Memory JSON file found at: {memory_file}")
            print(f"Raw contents: {memory_file.read_text(encoding='utf-8')}")
        else:
            print("Memory JSON file not found!")

        print("\nMemory session example finished successfully!")


if __name__ == "__main__":
    main()
