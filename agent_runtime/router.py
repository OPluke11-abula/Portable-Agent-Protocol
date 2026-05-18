"""Router that discovers tool modules and dispatches requests."""

from __future__ import annotations

import importlib
from typing import Any

from .logger import get_logger

logger = get_logger(__name__)

_TOOLS_PACKAGE = "agent_runtime.tools"


class Router:
    """Maps tool names to their ``run`` callables.

    Tool modules live in ``agent_runtime/tools/<name>.py`` and must expose a
    ``run(params: dict) -> dict`` function.
    """

    def __init__(self, tools: list[str] | None = None, mcp_servers: dict[str, Any] | None = None) -> None:
        self._registry: dict[str, Any] = {}
        for name in tools or []:
            self._register(name)
            
        if mcp_servers:
            self._mcp_servers = mcp_servers
        else:
            self._mcp_servers = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _register(self, name: str) -> None:
        module_path = f"{_TOOLS_PACKAGE}.{name}"
        try:
            module = importlib.import_module(module_path)
            if not hasattr(module, "run"):
                raise AttributeError(f"Tool module '{module_path}' has no 'run' function")
            self._registry[name] = module.run
            logger.debug("Registered tool: %s", name)
        except ImportError as exc:
            logger.warning("Could not import tool '%s': %s", name, exc)

    def register_tool(self, name: str, handler: Any) -> None:
        """Register an in-process tool handler for tests or host applications."""
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._registry[name] = handler
        logger.debug("Registered in-process tool: %s", name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def available_tools(self) -> list[str]:
        """Sorted list of registered tool names."""
        return sorted(self._registry)

    def route(self, tool: str, params: dict[str, Any]) -> dict[str, Any]:
        """Call *tool* with *params* and return its result dict.

        Raises ``KeyError`` if the tool is not registered.
        """
        # Check if it's an MCP tool (format: mcp_{server_name}_{tool_name})
        if tool.startswith("mcp_"):
            parts = tool.split("_", 2)
            if len(parts) >= 3:
                server_name = parts[1]
                mcp_tool_name = parts[2]
                
                if server_name in self._mcp_servers:
                    from .mcp_bridge import execute_mcp_tool
                    logger.debug("Routing to MCP server=%s tool=%s params=%s", server_name, mcp_tool_name, params)
                    return execute_mcp_tool(self._mcp_servers[server_name], mcp_tool_name, params)
                
        if tool not in self._registry:
            raise KeyError(
                f"Unknown tool '{tool}'. Available local: {self.available_tools}"
            )
        logger.debug("Routing to local tool=%s params=%s", tool, params)
        return self._registry[tool](params)
