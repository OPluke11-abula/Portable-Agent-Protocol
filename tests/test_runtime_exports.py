"""Tests for lazy top-level runtime exports."""

from __future__ import annotations

import pytest

import agent_runtime


def test_lazy_exports_resolve_public_runtime_symbols() -> None:
    assert agent_runtime.AgentEngine.__name__ == "AgentEngine"
    assert agent_runtime.load_agent_config.__name__ == "load_agent_config"
    assert agent_runtime.load_agent_layout.__name__ == "load_agent_layout"
    assert agent_runtime.Router.__name__ == "Router"
    assert agent_runtime.get_logger.__name__ == "get_logger"

    assert agent_runtime.MemoryBackend.__name__ == "MemoryBackend"
    assert agent_runtime.InMemoryBackend.__name__ == "InMemoryBackend"
    assert agent_runtime.JSONFileBackend.__name__ == "JSONFileBackend"
    assert agent_runtime.SQLiteBackend.__name__ == "SQLiteBackend"
    assert agent_runtime.VectorDBBackend.__name__ == "VectorDBBackend"
    assert agent_runtime.create_memory_backend.__name__ == "create_memory_backend"

    assert agent_runtime.WorkflowExecutor.__name__ == "WorkflowExecutor"
    assert agent_runtime.WorkflowEngine.__name__ == "WorkflowEngine"
    assert agent_runtime.DAG.__name__ == "DAG"
    assert agent_runtime.Step.__name__ == "Step"

    assert agent_runtime.KnowledgeBase.__name__ == "KnowledgeBase"
    assert agent_runtime.PromptComposer.__name__ == "PromptComposer"
    assert agent_runtime.SafePromptString.__name__ == "SafePromptString"
    assert agent_runtime.validate_prompt_string.__name__ == "validate_prompt_string"


def test_lazy_exports_reject_unknown_symbol() -> None:
    with pytest.raises(AttributeError, match="does_not_exist"):
        getattr(agent_runtime, "does_not_exist")
