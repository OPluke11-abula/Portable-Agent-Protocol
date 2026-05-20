"""Tests for protocol and runtime version compatibility checking in AgentEngine."""

from __future__ import annotations

import logging
from pathlib import Path
import pytest

from agent_runtime.engine import AgentEngine, parse_version


def test_parse_version() -> None:
    assert parse_version("1.2.3") == (1, 2, 3)
    assert parse_version("v2.0.0") == (2, 0, 0)
    assert parse_version("0.1.0-alpha") == (0, 1, 0)
    assert parse_version("v3") == (3, 0, 0)
    assert parse_version("invalid") == (0, 0, 0)


def _write_temp_agent_config(tmp_path: Path, protocol_ver: str, min_runtime_ver: str) -> Path:
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    
    # Create empty directories to satisfy path checks
    (agent_dir / "skills").mkdir(exist_ok=True)
    (agent_dir / "workflows").mkdir(exist_ok=True)
    (agent_dir / "memory").mkdir(exist_ok=True)

    config_content = f"""---
protocol_version: "{protocol_ver}"
min_runtime_version: "{min_runtime_ver}"
name: test-compat-agent
version: 0.1.0
purpose: Test compatibility.
language: en-US
authorization_level: read-only
use_case_tags: [test]
tools: []
protocol:
  root: .agent/
  manifest: .agent/agent.md
  directories:
    skills: .agent/skills/
    workflows: .agent/workflows/
memory:
  backend: local
  path: .agent/memory/
---
# Test Compat Agent
"""
    config_path = agent_dir / "agent.md"
    config_path.write_text(config_content, encoding="utf-8")
    return config_path


def test_version_compat_ok(caplog, tmp_path) -> None:
    config_path = _write_temp_agent_config(tmp_path, "1.0.0", "0.1.0")
    
    with caplog.at_level(logging.WARNING):
        engine = AgentEngine(config_path=config_path)
    
    warnings = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert not any("requires minimum runtime version" in w for w in warnings)
    assert not any("uses protocol version" in w for w in warnings)
    assert engine.config["protocol_version"] == "1.0.0"


def test_version_compat_runtime_outdated(caplog, tmp_path) -> None:
    # Set min_runtime_version to 9.9.9 (far greater than current 0.1.0)
    config_path = _write_temp_agent_config(tmp_path, "1.0.0", "9.9.9")
    
    with caplog.at_level(logging.WARNING):
        engine = AgentEngine(config_path=config_path)
    
    warnings = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any("requires minimum runtime version 9.9.9" in w for w in warnings)


def test_version_compat_protocol_mismatch(caplog, tmp_path) -> None:
    # Set protocol_version to 2.0.0 (current supported is 1.0.0, major mismatch)
    config_path = _write_temp_agent_config(tmp_path, "2.0.0", "0.1.0")
    
    with caplog.at_level(logging.WARNING):
        engine = AgentEngine(config_path=config_path)
    
    warnings = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any("uses protocol version 2.0.0, but the runtime supports protocol version 1.0.0" in w for w in warnings)
