"""Tests for the Cross-Agent Handoff Mechanism (Phase 1-04).

Validates exporting handoff packets, checksum generation, integrity checking on import,
schema conformance, and memory restoration.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agent_runtime.engine import AgentEngine


def _setup_mock_agent(tmp_path: Path, subdir: str = "") -> AgentEngine:
    """Helper to scaffold a temporary agent configuration for testing handoffs."""
    base_dir = tmp_path
    if subdir:
        base_dir = tmp_path / subdir

    agent_dir = base_dir / ".agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    memory_dir = agent_dir / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)

    agent_config = textwrap.dedent(
        f"""\
        ---
        protocol_version: "1.0.0"
        min_runtime_version: "0.1.0"
        name: handoff-test-agent
        version: "0.1.0"
        purpose: Test cross-agent handoff mechanics.
        language: en-US
        authorization_level: interactive-approval
        use_case_tags: [test]
        tools: []
        protocol:
          root: .agent/
          manifest: .agent/agent.md
          directories:
            memory: .agent/memory/
        memory:
          backend: local
          path: {memory_dir.as_posix()}
        ---
        # Handoff Test Agent
        """
    )
    (agent_dir / "agent.md").write_text(agent_config, encoding="utf-8")
    
    # Mock spec directory so that memory.schema.json can be loaded correctly
    spec_dir = base_dir / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy real memory schema to the temporary spec directory for validation testing
    real_schema_path = Path("spec/memory.schema.json")
    if real_schema_path.exists():
        (spec_dir / "memory.schema.json").write_text(real_schema_path.read_text(encoding="utf-8"), encoding="utf-8")

    return AgentEngine(config_path=agent_dir / "agent.md")


class TestCrossAgentHandoff:
    def test_export_and_import_success(self, tmp_path: Path) -> None:
        engine_src = _setup_mock_agent(tmp_path, "agent_src")
        
        # Populate source memory
        engine_src.memory.write("key1", "value1")
        engine_src.memory.write("key2", {"nested": "value2"})
        
        # Export handoff
        task_state = "Refactoring engine complete."
        pending_steps = ["Run benchmarks", "Write documentation"]
        context_summary = "All unit tests pass. Handoff to coder."
        
        handoff_id = engine_src.export_handoff(
            task_state=task_state,
            pending_steps=pending_steps,
            context_summary=context_summary,
            memory_keys=["key1", "key2"],
            handoff_id="test-handoff-1"
        )
        
        assert handoff_id == "test-handoff-1"
        
        # Verify the handoff file exists
        handoff_file_src = tmp_path / "agent_src" / ".agent" / "memory" / "handoff" / "test-handoff-1.json"
        assert handoff_file_src.exists()
        
        # Verify schema/structure of file content
        with handoff_file_src.open(encoding="utf-8") as f:
            data = json.load(f)
        assert data["task_state"] == task_state
        assert data["pending_steps"] == pending_steps
        assert data["context_summary"] == context_summary
        assert data["memory_snapshot"] == {
            "key1": "value1",
            "key2": {"nested": "value2"}
        }
        assert "checksum" in data

        # Load fresh engine to simulate the receiving agent in a different directory
        engine_dest = _setup_mock_agent(tmp_path, "agent_dest")
        assert engine_dest.memory.read("key1") is None
        
        # Simulate handoff file transfer by copying it to the destination's handoff folder
        handoff_file_dest = tmp_path / "agent_dest" / ".agent" / "memory" / "handoff" / "test-handoff-1.json"
        handoff_file_dest.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(handoff_file_src, handoff_file_dest)
        
        # Import the handoff packet
        imported_packet = engine_dest.import_handoff("test-handoff-1")
        
        # Verify contents are correct
        assert imported_packet["task_state"] == task_state
        assert imported_packet["pending_steps"] == pending_steps
        assert imported_packet["context_summary"] == context_summary
        
        # Verify memory was successfully restored in engine_dest
        assert engine_dest.memory.read("key1") == "value1"
        assert engine_dest.memory.read("key2") == {"nested": "value2"}

    def test_import_detects_corrupted_payload(self, tmp_path: Path) -> None:
        engine = _setup_mock_agent(tmp_path)
        
        # Write clean packet first
        handoff_id = engine.export_handoff(
            task_state="Active task state",
            pending_steps=["Task A"],
            context_summary="Context desc",
            memory_keys=[],
            handoff_id="corrupt-test"
        )
        
        handoff_file = tmp_path / ".agent" / "memory" / "handoff" / "corrupt-test.json"
        assert handoff_file.exists()
        
        # Intentionally alter content in the file without updating checksum
        with handoff_file.open(encoding="utf-8") as f:
            data = json.load(f)
        
        data["task_state"] = "Altered malicious state"
        
        with handoff_file.open("w", encoding="utf-8") as f:
            json.dump(data, f)
            
        # Receiver importing should throw Integrity check failed exception
        engine_receiver = _setup_mock_agent(tmp_path)
        with pytest.raises(ValueError, match="Handoff packet integrity check failed"):
            engine_receiver.import_handoff("corrupt-test")

    def test_import_missing_checksum_raises(self, tmp_path: Path) -> None:
        engine = _setup_mock_agent(tmp_path)
        
        # Write clean packet first
        engine.export_handoff(
            task_state="Active state",
            pending_steps=["Task"],
            context_summary="Summary",
            memory_keys=[],
            handoff_id="missing-checksum"
        )
        
        handoff_file = tmp_path / ".agent" / "memory" / "handoff" / "missing-checksum.json"
        
        # Remove checksum property completely
        with handoff_file.open(encoding="utf-8") as f:
            data = json.load(f)
        
        data.pop("checksum", None)
        
        with handoff_file.open("w", encoding="utf-8") as f:
            json.dump(data, f)
            
        with pytest.raises(ValueError, match="missing checksum"):
            engine.import_handoff("missing-checksum")

    def test_export_all_keys_when_none_specified(self, tmp_path: Path) -> None:
        engine = _setup_mock_agent(tmp_path)
        engine.memory.write("x", 1)
        engine.memory.write("y", 2)
        
        handoff_id = engine.export_handoff(
            task_state="State",
            pending_steps=[],
            context_summary="Ctx",
            memory_keys=None,  # default behavior should snap all keys
            handoff_id="all-keys-test"
        )
        
        handoff_file = tmp_path / ".agent" / "memory" / "handoff" / "all-keys-test.json"
        with handoff_file.open(encoding="utf-8") as f:
            data = json.load(f)
            
        assert data["memory_snapshot"] == {"x": 1, "y": 2}
