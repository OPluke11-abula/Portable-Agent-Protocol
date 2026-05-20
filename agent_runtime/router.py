"""Router that discovers tool modules, validates inputs against contracts, and dispatches requests."""

from __future__ import annotations

import importlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

import yaml

from .logger import get_logger

logger = get_logger(__name__)

_TOOLS_PACKAGE = "agent_runtime.tools"
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class Router:
    """Maps tool names to their ``run`` callables, validating inputs against contracts.

    Tool modules live in ``agent_runtime/tools/<name>.py`` and must expose a
    ``run(params: dict) -> dict`` function.
    """

    def __init__(
        self,
        tools: list[str] | None = None,
        mcp_servers: dict[str, Any] | None = None,
        skills_dir: str | Path | None = None,
    ) -> None:
        self._registry: dict[str, Any] = {}
        for name in tools or []:
            self._register(name)
            
        if mcp_servers:
            self._mcp_servers = mcp_servers
        else:
            self._mcp_servers = {}

        if skills_dir is not None:
            self._skills_dir = Path(skills_dir)
        else:
            self._skills_dir = Path(".agent/skills")

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

    def _load_contract(self, skill_id: str) -> dict[str, Any] | None:
        """Loads and parses the YAML front-matter of the skill contract for ``skill_id``."""
        if not self._skills_dir:
            return None

        contract_path = self._skills_dir / f"{skill_id}.md"
        if not contract_path.exists():
            return None

        try:
            text = contract_path.read_text(encoding="utf-8")
            match = _FRONTMATTER_RE.match(text)
            if not match:
                logger.warning("No YAML front-matter found in skill contract: %s", contract_path)
                return None
            return yaml.safe_load(match.group(1)) or {}
        except Exception as exc:
            logger.warning("Error reading skill contract %s: %s", contract_path, exc)
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def available_tools(self) -> list[str]:
        """Sorted list of registered tool names."""
        return sorted(self._registry)

    def list_skills(self) -> list[dict[str, Any]]:
        """Returns a list of structured skill contracts for all active skills in the skills directory."""
        skills = []
        if not self._skills_dir or not self._skills_dir.exists():
            return skills

        for path in sorted(self._skills_dir.glob("*.md")):
            if path.name.startswith("_") or path.name == "README.md" or path.name == "__init__.md":
                continue
            skill_id = path.stem
            contract = self.describe_skill(skill_id)
            if contract:
                skills.append(contract)
        return skills

    def describe_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Returns the parsed contract content for a single skill_id, or None if not found."""
        return self._load_contract(skill_id)

    def validate_call(self, skill_id: str, params: dict[str, Any]) -> None:
        """Validates parameters for a skill call against its contract.

        Raises:
            ValueError: If validation fails.
        """
        contract = self.describe_skill(skill_id)
        if not contract:
            logger.warning("No skill contract found for '%s', skipping validation", skill_id)
            return

        inputs_def = contract.get("inputs")
        if not isinstance(inputs_def, dict):
            return

        for param_name, param_info in inputs_def.items():
            if not isinstance(param_info, dict):
                continue

            is_required = param_info.get("required", False)
            expected_type = param_info.get("type")

            # Check presence
            if param_name not in params:
                if is_required:
                    raise ValueError(
                        f"Validation failed for skill '{skill_id}': missing required input field '{param_name}'"
                    )
                continue

            # Check type of existing parameter
            val = params[param_name]
            if expected_type:
                type_ok = False
                expected_type_lower = expected_type.lower()

                if expected_type_lower == "string":
                    type_ok = isinstance(val, str)
                elif expected_type_lower == "boolean":
                    type_ok = isinstance(val, bool)
                elif expected_type_lower == "integer":
                    type_ok = isinstance(val, int) and not isinstance(val, bool)
                elif expected_type_lower in ("number", "float"):
                    type_ok = isinstance(val, (int, float)) and not isinstance(val, bool)
                elif expected_type_lower == "array":
                    type_ok = isinstance(val, list)
                elif expected_type_lower == "object":
                    type_ok = isinstance(val, dict)
                else:
                    # Generic fallback or wildcard (any type is ok)
                    type_ok = True

                if not type_ok:
                    actual_type = type(val).__name__
                    raise ValueError(
                        f"Validation failed for skill '{skill_id}': parameter '{param_name}' has invalid type. "
                        f"Expected '{expected_type}', got '{actual_type}'"
                    )

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
                    self.validate_call(tool, params)
                    return execute_mcp_tool(self._mcp_servers[server_name], mcp_tool_name, params)
                
        if tool not in self._registry:
            raise KeyError(
                f"Unknown tool '{tool}'. Available local: {self.available_tools}"
            )
        logger.debug("Routing to local tool=%s params=%s", tool, params)
        self.validate_call(tool, params)
        return self._registry[tool](params)
