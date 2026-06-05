"""Behavioral tests for the PAP MCP bridge using fake MCP modules."""

from __future__ import annotations

import asyncio
import importlib
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any


def _load_bridge_with_fake_mcp(monkeypatch):
    state: dict[str, Any] = {
        "tools": [],
        "call_result": SimpleNamespace(content=[], isError=False),
        "server_params": None,
    }

    class FakeServerParameters:
        def __init__(self, command: str, args: list[str], env: dict[str, str]) -> None:
            self.command = command
            self.args = args
            self.env = env

    class FakeClientSession:
        def __init__(self, read: str, write: str) -> None:
            self.read = read
            self.write = write

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def initialize(self) -> None:
            return None

        async def list_tools(self):
            return SimpleNamespace(tools=state["tools"])

        async def call_tool(self, tool_name: str, arguments: dict[str, Any]):
            state["called_tool"] = tool_name
            state["called_arguments"] = arguments
            return state["call_result"]

    class FakeStdioClient:
        def __init__(self, server_params: FakeServerParameters) -> None:
            state["server_params"] = server_params

        async def __aenter__(self):
            return "read", "write"

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

    def fake_stdio_client(server_params: FakeServerParameters) -> FakeStdioClient:
        return FakeStdioClient(server_params)

    mcp_module = types.ModuleType("mcp")
    mcp_module.ClientSession = FakeClientSession
    mcp_module.StdioServerParameters = FakeServerParameters
    client_module = types.ModuleType("mcp.client")
    stdio_module = types.ModuleType("mcp.client.stdio")
    stdio_module.stdio_client = fake_stdio_client
    client_module.stdio = stdio_module

    monkeypatch.setitem(sys.modules, "mcp", mcp_module)
    monkeypatch.setitem(sys.modules, "mcp.client", client_module)
    monkeypatch.setitem(sys.modules, "mcp.client.stdio", stdio_module)
    monkeypatch.delitem(sys.modules, "agent_runtime.mcp_bridge", raising=False)

    return importlib.import_module("agent_runtime.mcp_bridge"), state


def _template() -> str:
    return """# {{skill_name}}

{{short_description_under_50_chars}}
{{author_or_ai_generator}}
{{purpose_description}}

- `{{param_1_name}}` ({{type}}, **Required**): {{param_1_description}}
- `{{param_2_name}}` ({{type}}, Optional): {{param_2_description}}

{{success_format_description}}
{{error_format_description}}
{{constraint_1}}
{{constraint_2}}
{{error_condition_1}}
{{fallback_action_1}}
"""


def test_generate_skill_markdown_maps_mcp_schema_to_contract(monkeypatch) -> None:
    bridge, _state = _load_bridge_with_fake_mcp(monkeypatch)
    tool = SimpleNamespace(
        name="lookup",
        description="Lookup records from a local MCP server.",
        inputSchema={
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "limit": {"type": "integer", "description": "Maximum records."},
            },
            "required": ["query"],
        },
    )

    content = bridge._generate_skill_markdown(tool, "sqlite", _template())

    assert "# mcp_sqlite_lookup" in content
    assert "`query` (string, **Required**): Search query." in content
    assert "`limit` (integer, Optional): Maximum records." in content
    assert "pap-mcp-bridge (sqlite)" in content


def test_fetch_tools_returns_empty_for_missing_command(monkeypatch) -> None:
    bridge, _state = _load_bridge_with_fake_mcp(monkeypatch)

    assert asyncio.run(bridge._fetch_tools_from_server("broken", {})) == []


def test_sync_mcp_servers_generates_skill_contracts(monkeypatch, tmp_path: Path) -> None:
    bridge, state = _load_bridge_with_fake_mcp(monkeypatch)
    state["tools"] = [
        SimpleNamespace(
            name="lookup",
            description="Lookup records.",
            inputSchema={"properties": {}, "required": []},
        )
    ]
    skills_dir = tmp_path / ".agent" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "_template.md").write_text(_template(), encoding="utf-8")

    bridge.sync_mcp_servers(
        {
            "mcp_servers": {
                "sqlite": {
                    "command": "fake-server",
                    "args": ["--db", "test.db"],
                    "env": {"PAP_TEST_TOKEN": "redacted"},
                }
            },
            "protocol": {"directories": {"skills": ".agent/skills/"}},
        },
        tmp_path,
    )

    generated = skills_dir / "mcp_sqlite_lookup.md"
    assert generated.exists()
    assert "mcp_sqlite_lookup" in generated.read_text(encoding="utf-8")
    assert state["server_params"].command == "fake-server"
    assert state["server_params"].env["PAP_TEST_TOKEN"] == "redacted"


def test_execute_mcp_tool_serializes_content(monkeypatch) -> None:
    bridge, state = _load_bridge_with_fake_mcp(monkeypatch)
    state["call_result"] = SimpleNamespace(
        content=[SimpleNamespace(model_dump=lambda: {"type": "text", "text": "ok"})],
        isError=False,
    )

    result = bridge.execute_mcp_tool(
        {"command": "fake-server", "args": []},
        "lookup",
        {"query": "PAP"},
    )

    assert result == {"content": [{"type": "text", "text": "ok"}], "isError": False}
    assert state["called_tool"] == "lookup"
    assert state["called_arguments"] == {"query": "PAP"}
