"""Performance regression checks for the Portable Agent Protocol (Task 3-03)."""

from __future__ import annotations

import pytest
import time
from pathlib import Path

from agent_runtime import AgentEngine
from agent_runtime.memory import create_memory_backend
from agent_runtime.workflow_engine import WorkflowEngine


def test_manifest_loading_performance(tmp_path: Path) -> None:
    """Verify that AgentEngine bootstrap and manifest loading is fast."""
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / ".agent" / "agent.md"
    
    # Run 5 iterations to get a stable duration
    start = time.perf_counter()
    for _ in range(5):
        engine = AgentEngine(config_path, bypass_onboarding=True)
    duration_ms = ((time.perf_counter() - start) / 5) * 1000.0
    
    # Target: < 50ms (Allowing 120ms max to prevent flaky CI pipeline failures)
    assert duration_ms < 120.0, f"Manifest loading took too long: {duration_ms:.2f} ms"


def test_skill_registry_lookup_performance() -> None:
    """Verify that skill registry querying is extremely fast."""
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / ".agent" / "agent.md"
    engine = AgentEngine(config_path, bypass_onboarding=True)
    
    start = time.perf_counter()
    iterations = 200
    for _ in range(iterations):
        engine.router.describe_skill("search_web")
    duration_ms = ((time.perf_counter() - start) / iterations) * 1000.0
    
    # Target: < 10ms (Allowing 25ms max for virtualized CI)
    assert duration_ms < 25.0, f"Skill registry lookup took too long: {duration_ms:.4f} ms"


@pytest.mark.parametrize("backend_name", ["in_memory", "sqlite"])
def test_memory_reads_writes_performance(backend_name: str) -> None:
    """Verify that bulk read/write operations for 1000 entries are highly performant."""
    db_path = ":memory:" if backend_name == "sqlite" else None
    backend = create_memory_backend(backend_name, path=db_path)
    
    data = {f"key_{i}": f"value_{i}" for i in range(1000)}
    
    # Measure writes
    write_start = time.perf_counter()
    for k, v in data.items():
        backend.write(k, v)
    write_ms = (time.perf_counter() - write_start) * 1000.0
    
    # Measure reads
    read_start = time.perf_counter()
    for k in data.keys():
        backend.read(k)
    read_ms = (time.perf_counter() - read_start) * 1000.0
    
    # Cleanup
    for k in data.keys():
        backend.delete(k)
        
    # Target: < 100ms (Allowing 200ms max for virtualized environments)
    assert write_ms < 200.0, f"1000 writes for {backend_name} took too long: {write_ms:.2f} ms"
    assert read_ms < 200.0, f"1000 reads for {backend_name} took too long: {read_ms:.2f} ms"


def test_workflow_routing_performance() -> None:
    """Verify that parsing and initializing a workflow DAG is highly performant."""
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / ".agent" / "agent.md"
    engine = AgentEngine(config_path, bypass_onboarding=True)
    wf_engine = WorkflowEngine(engine)
    
    start = time.perf_counter()
    iterations = 50
    for _ in range(iterations):
        wf_engine.load("research_and_report")
    duration_ms = ((time.perf_counter() - start) / iterations) * 1000.0
    
    # Target: < 50ms (Allowing 100ms max for slow environments)
    assert duration_ms < 100.0, f"Workflow loading took too long: {duration_ms:.2f} ms"
