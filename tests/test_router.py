"""Tests for the Router and the full engine routing flow."""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import pytest

from agent_runtime.router import Router
from agent_runtime.engine import AgentEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_agent_md(tmp_path: Path, tools: list[str]) -> Path:
    tool_lines = "\n".join(f"  - {t}" for t in tools)
    content = textwrap.dedent(f"""\
        ---
        name: test-agent
        version: "0.1.0"
        tools:
        {tool_lines}
        ---
        # test
    """)
    p = tmp_path / "agent.md"
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Router unit tests
# ---------------------------------------------------------------------------

class TestRouter:
    def test_registers_known_tools(self) -> None:
        router = Router(tools=["search_web", "query_db", "code_executor"])
        assert set(router.available_tools) == {"search_web", "query_db", "code_executor"}

    def test_unknown_tool_raises_key_error(self) -> None:
        router = Router(tools=["search_web"])
        with pytest.raises(KeyError, match="no_such_tool"):
            router.route("no_such_tool", {})

    def test_missing_tool_module_is_skipped_gracefully(self) -> None:
        # "nonexistent_tool" has no module, but Router should not crash.
        router = Router(tools=["nonexistent_tool"])
        assert "nonexistent_tool" not in router.available_tools

    def test_available_tools_is_sorted(self) -> None:
        router = Router(tools=["query_db", "search_web", "code_executor"])
        assert router.available_tools == sorted(router.available_tools)


# ---------------------------------------------------------------------------
# Tool stub tests routed via Router
# ---------------------------------------------------------------------------

class TestSearchWebTool:
    def setup_method(self) -> None:
        self.router = Router(tools=["search_web"])

    def test_returns_results_list(self) -> None:
        result = self.router.route("search_web", {"query": "python", "limit": 3})
        assert "results" in result
        assert len(result["results"]) == 3

    def test_each_result_has_required_fields(self) -> None:
        result = self.router.route("search_web", {"query": "test"})
        for item in result["results"]:
            assert "title" in item
            assert "url" in item
            assert "snippet" in item

    def test_missing_query_returns_error(self) -> None:
        with pytest.raises(ValueError, match="missing required input field"):
            self.router.route("search_web", {})


class TestQueryDbTool:
    def setup_method(self) -> None:
        self.router = Router(tools=["query_db"])

    def test_returns_rows(self) -> None:
        result = self.router.route("query_db", {"connection_target": "default", "query_intent": "SELECT 1"})
        assert "rows" in result
        assert len(result["rows"]) >= 1

    def test_missing_sql_returns_error(self) -> None:
        with pytest.raises(ValueError, match="missing required input field"):
            self.router.route("query_db", {"connection_target": "default"})


class TestCodeExecutorTool:
    def setup_method(self) -> None:
        self.router = Router(tools=["code_executor"])

    def test_runs_simple_code(self) -> None:
        result = self.router.route("code_executor", {"runtime": "python", "command": "print('hello')"})
        assert result["exit_code"] == 0
        assert "hello" in result["stdout"]

    def test_captures_stderr(self) -> None:
        result = self.router.route(
            "code_executor", {"runtime": "python", "command": "import sys; sys.stderr.write('err\\n')"}
        )
        assert "err" in result["stderr"]

    def test_missing_code_returns_error(self) -> None:
        with pytest.raises(ValueError, match="missing required input field"):
            self.router.route("code_executor", {"runtime": "python"})

    def test_non_zero_exit_on_syntax_error(self) -> None:
        result = self.router.route("code_executor", {"runtime": "python", "command": "def broken syntax"})
        assert result["exit_code"] != 0


# ---------------------------------------------------------------------------
# AgentEngine integration tests
# ---------------------------------------------------------------------------

class TestAgentEngine:
    def test_engine_loads_config(self, tmp_path: Path) -> None:
        path = _write_agent_md(tmp_path, ["search_web"])
        engine = AgentEngine(config_path=path)
        assert engine.config["name"] == "test-agent"

    def test_engine_route_search_web(self, tmp_path: Path) -> None:
        path = _write_agent_md(tmp_path, ["search_web"])
        engine = AgentEngine(config_path=path)
        result = engine.run("search_web", {"query": "pytest", "limit": 2})
        assert len(result["results"]) == 2

    def test_engine_unknown_tool_raises(self, tmp_path: Path) -> None:
        path = _write_agent_md(tmp_path, ["search_web"])
        engine = AgentEngine(config_path=path)
        with pytest.raises(KeyError):
            engine.run("does_not_exist", {})
