"""Example 04: PAP Knowledge Base Query.

This script demonstrates how to query the local read-only knowledge base
and inspect documents using the AgentEngine knowledge base API.
"""

from __future__ import annotations

import json
import tempfile
import textwrap
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
            project_name="knowledge-project",
            agent_name="KnowledgeAgent",
            skills_list=[],
            dry_run=False
        )

        config_path = tmp_path / ".agent" / "agent.md"
        kb_dir = tmp_path / ".agent" / "knowledge_base"

        # 2. Add sample documents and index.json to knowledge base
        doc1_path = kb_dir / "protocol_spec.md"
        doc1_path.write_text(
            textwrap.dedent("""\
            ---
            id: protocol-spec
            title: PAP Protocol Specification
            tags: [protocol, spec, standard]
            created: "2026-05-20"
            updated: "2026-05-20"
            ---

            # Portable Agent Protocol Spec

            This standard defines files, schemas, and schemas for agents.
            """),
            encoding="utf-8"
        )

        doc2_path = kb_dir / "architecture.md"
        doc2_path.write_text(
            textwrap.dedent("""\
            ---
            id: architecture
            title: System Core Architecture
            tags: [design, system, architecture]
            created: "2026-05-20"
            updated: "2026-05-20"
            ---

            # System Core Architecture

            This describes the workflow topology, memory tiers, and execution flow.
            """),
            encoding="utf-8"
        )

        index_data = [
            {
                "id": "protocol-spec",
                "title": "PAP Protocol Specification",
                "path": str(doc1_path).replace("\\", "/"),
                "tags": ["protocol", "spec", "standard"],
                "created": "2026-05-20",
                "updated": "2026-05-20"
            },
            {
                "id": "architecture",
                "title": "System Core Architecture",
                "path": str(doc2_path).replace("\\", "/"),
                "tags": ["design", "system", "architecture"],
                "created": "2026-05-20",
                "updated": "2026-05-20"
            }
        ]
        (kb_dir / "index.json").write_text(json.dumps(index_data, indent=2), encoding="utf-8")

        # 3. Instantiate Agent Engine
        engine = AgentEngine(config_path)
        print("AgentEngine initialized.")

        # 4. List all knowledge base entries
        print("\n--- 1. Listing Knowledge Base Entries ---")
        entries = engine.knowledge_base.list_entries()
        for e in entries:
            print(f"ID: {e['id']} | Title: {e['title']} | Tags: {e['tags']}")

        # 5. Search using query
        print("\n--- 2. Performing Keyword Search ---")
        keyword = "architecture"
        print(f"Querying for: '{keyword}'")
        results = engine.knowledge_base.query(keyword)
        for r in results:
            print(f"Found Match: {r['title']} (ID: {r['id']})")

        # 6. Retrieve single document
        print("\n--- 3. Retrieving Single Document Details ---")
        doc_id = "protocol-spec"
        doc = engine.knowledge_base.get(doc_id)
        if doc:
            print(f"Title: {doc['title']}")
            print(f"Content:\n{doc['content'].strip()}")

        # 7. Verify write protection (strict read-only validation)
        print("\n--- 4. Verifying Write Protection ---")
        try:
            engine.knowledge_base.write("new-doc", {"title": "Attempt"})
            print("Error: Document creation unexpectedly succeeded!")
        except PermissionError as pe:
            print(f"Success: Write protection blocked write as expected: {pe}")

        print("\nKnowledge base query example finished successfully!")


if __name__ == "__main__":
    main()
