#!/usr/bin/env python3
"""Performance benchmarking suite for the Portable Agent Protocol (PAP)."""

import sys
import time
import json
import platform
from pathlib import Path

# Ensure the project root is in the python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from agent_runtime.engine import AgentEngine
from agent_runtime.memory import create_memory_backend
from agent_runtime.workflow_engine import WorkflowEngine


def get_env_info() -> dict:
    return {
        "python_version": platform.python_version(),
        "os": platform.system(),
        "os_release": platform.release(),
        "processor": platform.processor(),
    }


def run_benchmarks() -> dict:
    results = {}
    config_path = project_root / ".agent" / "agent.md"

    print("=" * 60)
    print(" PAP REFERENCE RUNTIME PERFORMANCE BENCHMARKS ")
    print("=" * 60)
    env_info = get_env_info()
    for k, v in env_info.items():
        print(f" {k.replace('_', ' ').title():<18}: {v}")
    print("-" * 60)

    # 1. Manifest Loading & Bootstrap Time
    print("1. Running Manifest Loading & Bootstrap Benchmark...")
    start_time = time.perf_counter()
    iterations = 50
    for _ in range(iterations):
        # Instantiate engine
        engine = AgentEngine(config_path, bypass_onboarding=True)
    end_time = time.perf_counter()
    avg_manifest_load_ms = ((end_time - start_time) / iterations) * 1000.0
    results["manifest_loading_ms"] = avg_manifest_load_ms
    print(f"   -> Average Manifest Loading: {avg_manifest_load_ms:.2f} ms")

    # 2. Skill Registry Lookup Time
    print("2. Running Skill Registry Lookup Benchmark...")
    engine = AgentEngine(config_path, bypass_onboarding=True)
    router = engine.router
    # Warmup
    router.describe_skill("search_web")
    
    start_time = time.perf_counter()
    lookup_iterations = 1000
    for _ in range(lookup_iterations):
        router.describe_skill("search_web")
    end_time = time.perf_counter()
    avg_lookup_ms = ((end_time - start_time) / lookup_iterations) * 1000.0
    results["skill_registry_lookup_ms"] = avg_lookup_ms
    print(f"   -> Average Skill Registry Lookup: {avg_lookup_ms:.4f} ms")

    # 3. Memory Reads & Writes Performance (1000 entries)
    print("3. Running Memory Reads & Writes Benchmark...")
    
    # We test both InMemoryBackend (ephemeral) and SQLiteBackend (in-memory SQLite)
    for backend_name in ["in_memory", "sqlite"]:
        db_path = ":memory:" if backend_name == "sqlite" else None
        backend = create_memory_backend(backend_name, path=db_path)
        
        # Prepare 1000 entries
        data = {f"key_{i}": f"value_{i}" for i in range(1000)}
        
        # Bulk Writes
        write_start = time.perf_counter()
        for k, v in data.items():
            backend.write(k, v)
        write_end = time.perf_counter()
        write_ms = (write_end - write_start) * 1000.0
        
        # Bulk Reads
        read_start = time.perf_counter()
        for k in data.keys():
            backend.read(k)
        read_end = time.perf_counter()
        read_ms = (read_end - read_start) * 1000.0
        
        # Cleanup
        for k in data.keys():
            backend.delete(k)
            
        results[f"memory_{backend_name}_write_1000_ms"] = write_ms
        results[f"memory_{backend_name}_read_1000_ms"] = read_ms
        print(f"   -> [{backend_name.upper()}] 1000 Writes: {write_ms:.2f} ms")
        print(f"   -> [{backend_name.upper()}] 1000 Reads:  {read_ms:.2f} ms")

    # 4. Workflow DAG parsing & routing Time
    print("4. Running Workflow Routing / DAG Parsing Benchmark...")
    wf_engine = WorkflowEngine(engine)
    # Warmup
    wf_engine.load("research_and_report")
    
    start_time = time.perf_counter()
    wf_iterations = 200
    for _ in range(wf_iterations):
        wf_engine.load("research_and_report")
    end_time = time.perf_counter()
    avg_wf_load_ms = ((end_time - start_time) / wf_iterations) * 1000.0
    results["workflow_routing_ms"] = avg_wf_load_ms
    print(f"   -> Average Workflow Load: {avg_wf_load_ms:.2f} ms")

    # Generate Performance Summary Table
    print("\n" + "=" * 70)
    print(f" {'INDICATOR':<35} | {'TARGET':<10} | {'MEASURED':<10} | {'STATUS':<6}")
    print("=" * 70)
    
    targets = {
        "manifest_loading_ms": 50.0,
        "skill_registry_lookup_ms": 10.0,
        "memory_in_memory_write_1000_ms": 100.0,
        "memory_in_memory_read_1000_ms": 100.0,
        "memory_sqlite_write_1000_ms": 100.0,
        "memory_sqlite_read_1000_ms": 100.0,
        "workflow_routing_ms": 50.0,  # Target reasonable workflow load limit
    }
    
    pretty_names = {
        "manifest_loading_ms": "Manifest Loading (Engine Bootstrap)",
        "skill_registry_lookup_ms": "Skill Registry Lookup",
        "memory_in_memory_write_1000_ms": "Memory 1000 Writes (InMemory)",
        "memory_in_memory_read_1000_ms": "Memory 1000 Reads (InMemory)",
        "memory_sqlite_write_1000_ms": "Memory 1000 Writes (SQLite-Mem)",
        "memory_sqlite_read_1000_ms": "Memory 1000 Reads (SQLite-Mem)",
        "workflow_routing_ms": "Workflow Routing / DAG Load",
    }
    
    for metric, target in targets.items():
        val = results[metric]
        status = "PASS" if val < target else "FAIL"
        print(f" {pretty_names[metric]:<35} | < {target:<5} ms | {val:<7.2f} ms | {status}")
        
    print("=" * 70)

    # Save to report.json
    report_data = {
        "environment": env_info,
        "metrics": results,
        "targets": targets,
    }
    report_path = project_root / "benchmarks" / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"\nSaved performance benchmark report to: {report_path}\n")
    
    return results


if __name__ == "__main__":
    run_benchmarks()
