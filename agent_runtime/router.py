"""Router that discovers tool modules, validates inputs against contracts, and dispatches requests."""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any, Callable

import yaml

from .logger import get_logger

logger = get_logger(__name__)

_TOOLS_PACKAGE = "agent_runtime.tools"
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def validate_skill_id(skill_id: str) -> None:
    """Validate skill_id format to prevent path traversal and arbitrary file reads.

    Raises ValueError if skill_id contains path separators, parent references, or invalid characters.
    """
    if not isinstance(skill_id, str):
        raise TypeError("skill_id must be a string")
    if not skill_id:
        raise ValueError("skill_id cannot be empty")
    # Strictly allow alphanumeric, hyphens, and underscores
    if not re.match(r"^[a-zA-Z0-9_-]+$", skill_id):
        raise ValueError(
            f"Invalid skill_id format: '{skill_id}'. Only alphanumeric characters, hyphens, and underscores are allowed."
        )


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
        onboarding_guard: Callable[[], None] | None = None,
        tool_manifest: Any | None = None,
    ) -> None:
        self._registry: dict[str, Any] = {}
        self._onboarding_guard = onboarding_guard
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

        from .tool_manifest import ToolManifest
        if tool_manifest is not None:
            self._tool_manifest = tool_manifest
        else:
            self._tool_manifest = ToolManifest(local_skills_dir=self._skills_dir)

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

    def set_onboarding_guard(self, guard: Callable[[], None] | None) -> None:
        """Set a runtime guard that must pass before dispatching any tool."""
        self._onboarding_guard = guard

    def _load_contract(self, skill_id: str) -> dict[str, Any] | None:
        """Loads and parses the YAML front-matter of the skill contract for ``skill_id``."""
        validate_skill_id(skill_id)
        contract_path = None
        if hasattr(self, "_tool_manifest") and self._tool_manifest is not None:
            contract_path = self._tool_manifest.get_skill_contract_path(skill_id)

        if not contract_path:
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
            data = yaml.safe_load(match.group(1)) or {}
            if not isinstance(data, dict):
                data = {}
            if data.get("status") == "draft" or "drafts" in contract_path.parts:
                logger.debug("Skill contract %s is a draft, refusing to load officially", contract_path)
                return None
            if not data.get("id"):
                data["id"] = skill_id
            if not data.get("name"):
                data["name"] = data["id"]
            if data.get("description") is None:
                data["description"] = ""
            if not data.get("version"):
                data["version"] = "1.0.0"
            if data.get("inputs") is None:
                data["inputs"] = {}
            if data.get("outputs") is None:
                data["outputs"] = {}
            if data.get("safety_notes") is None:
                data["safety_notes"] = []
            return data
        except Exception as exc:
            logger.warning("Error reading skill contract %s: %s", contract_path, exc)
            return None

    def is_registered_in_active_registry(self, skill_id: str) -> bool:
        """Checks if a skill contract file exists on disk and is NOT a draft."""
        try:
            validate_skill_id(skill_id)
        except (TypeError, ValueError):
            return False

        contract_path = None
        if hasattr(self, "_tool_manifest") and self._tool_manifest is not None:
            contract_path = self._tool_manifest.get_skill_contract_path(skill_id)

        if not contract_path:
            if not self._skills_dir:
                return False
            contract_path = self._skills_dir / f"{skill_id}.md"

        if not contract_path.exists():
            return False

        if "drafts" in contract_path.parts:
            return False

        try:
            text = contract_path.read_text(encoding="utf-8")
            match = _FRONTMATTER_RE.match(text)
            if match:
                data = yaml.safe_load(match.group(1)) or {}
                if isinstance(data, dict) and data.get("status") == "draft":
                    return False
        except Exception:
            pass

        return True

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
        skill_ids = set()
        if hasattr(self, "_tool_manifest") and self._tool_manifest is not None:
            for skill_id in self._tool_manifest.list_all():
                skill_ids.add(skill_id)
        else:
            if self._skills_dir and self._skills_dir.exists():
                for path in self._skills_dir.glob("*.md"):
                    if path.name.startswith("_") or path.name in ("README.md", "__init__.md"):
                        continue
                    skill_ids.add(path.stem)

        for skill_id in sorted(list(skill_ids)):
            contract = self.describe_skill(skill_id)
            if contract:
                skills.append(contract)
        return skills

    def describe_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Returns the parsed contract content for a single skill_id, or None if not found."""
        validate_skill_id(skill_id)
        return self._load_contract(skill_id)

    def validate_call(self, skill_id: str, params: dict[str, Any]) -> None:
        """Validates parameters for a skill call against its contract.

        Raises:
            ValueError: If validation fails.
        """
        validate_skill_id(skill_id)
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

            # Enforce exact type declaration in skill contract
            if not expected_type or not isinstance(expected_type, str) or expected_type.lower() not in ("string", "boolean", "integer", "number", "float", "array", "object"):
                raise ValueError(
                    f"Validation failed for skill '{skill_id}': input field '{param_name}' must declare a strict exact JSON type "
                    f"('string', 'integer', 'boolean', 'number', 'float', 'array', 'object'). Got: '{expected_type}'"
                )

            # Check presence
            if param_name not in params:
                if is_required:
                    raise ValueError(
                        f"Validation failed for skill '{skill_id}': missing required input field '{param_name}'"
                    )
                continue

            # Check type of existing parameter
            val = params[param_name]
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
        if self._onboarding_guard is not None:
            self._onboarding_guard()

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
