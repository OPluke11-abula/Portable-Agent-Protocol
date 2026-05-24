"""Tests for standard memory directories, schemas, samples, and query interface."""

from __future__ import annotations

import textwrap
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from typing import Any

import pytest

try:
    import jsonschema
except ImportError:
    jsonschema = None

from agent_runtime.memory import (
    InMemoryBackend,
    JSONFileBackend,
    SQLiteBackend,
    create_memory_backend,
)
from agent_runtime.engine import AgentEngine


def test_memory_directories_and_readmes() -> None:
    """Verify that episodic, semantic, and handoff memory directories and READMEs exist."""
    base_dir = Path(".agent/memory")
    assert base_dir.exists()
    assert base_dir.is_dir()

    for tier in ("episodic", "semantic", "handoff"):
        tier_dir = base_dir / tier
        assert tier_dir.exists(), f"Memory tier directory '{tier}' is missing."
        assert tier_dir.is_dir()

        readme = tier_dir / "README.md"
        assert readme.exists(), f"README.md is missing in memory tier '{tier}'."
        assert readme.is_file()
        assert len(readme.read_text(encoding="utf-8").strip()) > 0


def test_schema_file_exists() -> None:
    """Verify that .agent/memory/schema.json exists and is a valid JSON schema."""
    schema_path = Path(".agent/memory/schema.json")
    assert schema_path.exists()
    assert schema_path.is_file()

    # Verify it is valid JSON
    with schema_path.open(encoding="utf-8") as f:
        schema = json.load(f)
    
    assert schema.get("$schema") is not None
    assert "properties" in schema
    assert "$defs" in schema


def test_episodic_sample_format() -> None:
    """Verify examples/memory_episodic_sample.jsonl is valid JSONLines and parses correctly."""
    sample_path = Path("examples/memory_episodic_sample.jsonl")
    assert sample_path.exists()
    assert sample_path.is_file()

    with sample_path.open(encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert len(lines) > 0
    for idx, line in enumerate(lines):
        record = json.loads(line)
        assert "id" in record, f"Line {idx} missing 'id'"
        assert "timestamp" in record, f"Line {idx} missing 'timestamp'"
        assert "role" in record, f"Line {idx} missing 'role'"
        assert "content" in record, f"Line {idx} missing 'content'"


def test_semantic_sample_format() -> None:
    """Verify examples/memory_semantic_sample.json is valid JSON and parses correctly."""
    sample_path = Path("examples/memory_semantic_sample.json")
    assert sample_path.exists()
    assert sample_path.is_file()

    with sample_path.open(encoding="utf-8") as f:
        record = json.load(f)

    assert "key" in record
    assert "value" in record


def test_handoff_sample_format() -> None:
    """Verify examples/memory_handoff_sample.json is valid JSON and parses correctly."""
    sample_path = Path("examples/memory_handoff_sample.json")
    assert sample_path.exists()
    assert sample_path.is_file()

    with sample_path.open(encoding="utf-8") as f:
        record = json.load(f)

    assert "task_state" in record
    assert "pending_steps" in record
    assert "context_summary" in record
    assert "memory_snapshot" in record


@pytest.mark.skipif(jsonschema is None, reason="jsonschema package not installed")
def test_samples_against_memory_schema() -> None:
    """Validate sample files against local .agent/memory/schema.json if jsonschema is available."""
    schema_path = Path(".agent/memory/schema.json")
    with schema_path.open(encoding="utf-8") as f:
        schema = json.load(f)

    # Validate episodic sample
    episodic_def = schema["$defs"]["episodic_entry"]
    episodic_schema = {
        "$schema": schema.get("$schema"),
        **episodic_def,
        "$defs": schema.get("$defs", {}),
    }
    episodic_sample_path = Path("examples/memory_episodic_sample.jsonl")
    with episodic_sample_path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                jsonschema.validate(instance=record, schema=episodic_schema)

    # Validate semantic sample
    semantic_def = schema["$defs"]["semantic_record"]
    semantic_schema = {
        "$schema": schema.get("$schema"),
        **semantic_def,
        "$defs": schema.get("$defs", {}),
    }
    semantic_sample_path = Path("examples/memory_semantic_sample.json")
    with semantic_sample_path.open(encoding="utf-8") as f:
        record = json.load(f)
    jsonschema.validate(instance=record, schema=semantic_schema)

    # Validate handoff sample
    handoff_def = schema["$defs"]["handoff_packet"]
    handoff_schema = {
        "$schema": schema.get("$schema"),
        **handoff_def,
        "$defs": schema.get("$defs", {}),
    }
    handoff_sample_path = Path("examples/memory_handoff_sample.json")
    with handoff_sample_path.open(encoding="utf-8") as f:
        record = json.load(f)
    jsonschema.validate(instance=record, schema=handoff_schema)


def test_memory_backends_query_method(tmp_path: Path) -> None:
    """Verify that the new query method works seamlessly across all backends."""
    
    # 1. InMemoryBackend
    in_mem = create_memory_backend("in_memory")
    in_mem.write("app_key", "important_value")
    in_mem.write("other_key", "another_value")
    
    results = in_mem.query("important")
    assert len(results) == 1
    assert results[0]["key"] == "app_key"
    assert results[0]["value"] == "important_value"

    # 2. JSONFileBackend
    json_path = tmp_path / "memory_json"
    json_backend = JSONFileBackend(path=json_path)
    json_backend.write("setting_key", "test_query_value")
    json_backend.write("name_key", "protocol_test")
    
    results = json_backend.query("test_query")
    assert len(results) == 1
    assert results[0]["key"] == "setting_key"
    assert results[0]["value"] == "test_query_value"

    # 3. SQLiteBackend
    db_path = tmp_path / "test_memory.db"
    sqlite_backend = SQLiteBackend(db_path=db_path)
    sqlite_backend.write("db_key", "sqlite_val")
    sqlite_backend.write("unused_key", "something_else")
    
    results = sqlite_backend.query("sqlite")
    assert len(results) == 1
    assert results[0]["key"] == "db_key"
    assert results[0]["value"] == "sqlite_val"


def test_engine_memory_tiers_keep_scope_isolated(tmp_path: Path) -> None:
    """Tiered memory backends do not leak keys across runtime scopes."""
    agent_dir = tmp_path / ".agent"
    for child in ("skills", "workflows", "memory", "knowledge_base"):
        (agent_dir / child).mkdir(parents=True, exist_ok=True)

    memory_path = (agent_dir / "memory").as_posix()
    config = textwrap.dedent(
        f"""\
        ---
        protocol_version: "1.0.0"
        min_runtime_version: "0.1.0"
        name: memory-tier-agent
        version: "0.1.0"
        purpose: Verify memory tier isolation.
        language: en-US
        authorization_level: interactive-approval
        use_case_tags: [test]
        tools: []
        protocol:
          root: .agent/
          manifest: .agent/agent.md
          directories:
            skills: .agent/skills/
            workflows: .agent/workflows/
            memory: .agent/memory/
            knowledge_base: .agent/knowledge_base/
        memory:
          tiers:
            ephemeral: in_memory
            session: in_memory
            persistent: local
          path: "{memory_path}"
        ---
        # Memory Tier Agent
        """
    )
    config_path = agent_dir / "agent.md"
    config_path.write_text(config, encoding="utf-8")

    engine = AgentEngine(config_path)
    engine.memory_tiers["ephemeral"].write("scope", "ephemeral")
    engine.memory_tiers["session"].write("scope", "session")
    engine.memory_tiers["persistent"].write("scope", "persistent")

    assert engine.memory_tiers["ephemeral"].read("scope") == "ephemeral"
    assert engine.memory_tiers["session"].read("scope") == "session"
    assert engine.memory_tiers["persistent"].read("scope") == "persistent"
    assert engine.memory.read("scope") == "persistent"
    assert engine.memory_tiers["ephemeral"].list_keys() == ["scope"]
    assert engine.memory_tiers["session"].list_keys() == ["scope"]


def test_json_memory_backend_concurrent_writes_preserve_all_keys(tmp_path: Path) -> None:
    """A shared JSON backend instance serializes concurrent read/write access."""
    backend = JSONFileBackend(tmp_path / "memory")

    def write_entry(index: int) -> None:
        key = f"entry-{index:03d}"
        backend.write(key, {"index": index})
        assert backend.read(key) == {"index": index}

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(write_entry, range(64)))

    assert len(backend.list_keys()) == 64
    assert backend.read("entry-000") == {"index": 0}
    assert backend.read("entry-063") == {"index": 63}


def test_sqlite_memory_backend_handles_large_data_volume(tmp_path: Path) -> None:
    """The durable SQLite backend remains queryable with hundreds of records."""
    backend = SQLiteBackend(db_path=tmp_path / "memory.db")

    for index in range(500):
        backend.write(
            f"entry-{index:03d}",
            {"index": index, "payload": "x" * 128},
        )

    assert len(backend.list_keys()) == 500
    assert backend.read("entry-499") == {"index": 499, "payload": "x" * 128}

    matches = backend.search("entry-49", top_k=20)
    assert len(matches) == 10
    assert {match["key"] for match in matches} == {
        f"entry-49{suffix}" for suffix in range(10)
    }
