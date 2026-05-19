"""Router that discovers tool modules and dispatches requests."""

from __future__ import annotations

import importlib
import json
import os
import uuid
from pathlib import Path
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

    def dispatch_via_claude_api(
        self,
        tool_name: str,
        params: dict,
        skill_path: Path,
        memory_context: dict | None = None,
    ) -> dict:
        """Dispatch a skill through Claude API with PAP memory context."""
        from .memory.writeback import load_skill_memory, write_skill_result

        path = Path(skill_path)
        if not path.exists():
            raise FileNotFoundError(f"Skill file not found: {path}")

        agent_dir = self._infer_agent_dir(path)
        recent_memory = load_skill_memory(tool_name, agent_dir)
        prompt = self._build_claude_skill_prompt(
            tool_name=tool_name,
            params=params,
            skill_text=path.read_text(encoding="utf-8"),
            recent_memory=recent_memory,
            memory_context=memory_context,
        )
        skill_ref = self._resolve_anthropic_skill_ref(tool_name, params)
        result = self._call_claude_api(prompt, skill_ref=skill_ref)
        session_id = str(params.get("session_id") or uuid.uuid4())
        write_skill_result(tool_name, params, result, agent_dir, session_id)
        return result

    def _resolve_anthropic_skill_ref(self, tool_name: str, params: dict) -> dict[str, Any] | None:
        raw_ref = params.get("anthropic_skill")
        if isinstance(raw_ref, dict) and raw_ref.get("skill_id"):
            ref = {
                "type": raw_ref.get("type") or raw_ref.get("source") or "custom",
                "skill_id": raw_ref["skill_id"],
            }
            if raw_ref.get("version"):
                ref["version"] = raw_ref["version"]
            return ref

        env_key = re_safe_env_key(tool_name)
        skill_id = (
            params.get("anthropic_skill_id")
            or os.environ.get(f"ANTHROPIC_SKILL_ID_{env_key}")
        )
        if not skill_id and tool_name in {"docx", "pdf", "pptx", "xlsx"}:
            skill_id = tool_name

        if not skill_id:
            return None

        source = (
            params.get("anthropic_skill_type")
            or params.get("anthropic_skill_source")
            or os.environ.get(f"ANTHROPIC_SKILL_TYPE_{env_key}")
            or ("anthropic" if skill_id == tool_name and tool_name in {"docx", "pdf", "pptx", "xlsx"} else "custom")
        )
        ref = {"type": source, "skill_id": skill_id}
        version = (
            params.get("anthropic_skill_version")
            or os.environ.get(f"ANTHROPIC_SKILL_VERSION_{env_key}")
            or "latest"
        )
        if version:
            ref["version"] = version
        return ref

    def _infer_agent_dir(self, skill_path: Path) -> Path:
        for parent in [skill_path, *skill_path.parents]:
            if parent.name == ".agent":
                return parent
        cwd_agent = Path.cwd() / ".agent"
        return cwd_agent if cwd_agent.exists() else Path(".agent")

    def _build_claude_skill_prompt(
        self,
        *,
        tool_name: str,
        params: dict,
        skill_text: str,
        recent_memory: list[dict],
        memory_context: dict | None,
    ) -> str:
        payload = {
            "tool_name": tool_name,
            "params": params,
            "memory_context": memory_context or {},
            "recent_skill_memory": recent_memory,
        }
        return (
            "Execute the following Anthropic-compatible skill for a Portable "
            "Agent Protocol runtime. Return a concise JSON-compatible result.\n\n"
            "## Skill\n\n"
            f"{skill_text}\n\n"
            "## Runtime Context\n\n"
            "```json\n"
            f"{json.dumps(payload, indent=2, ensure_ascii=False)}\n"
            "```"
        )

    def _call_claude_api(self, prompt: str, skill_ref: dict[str, Any] | None = None) -> dict:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for Claude API dispatch")

        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError(
                "The optional 'anthropic' dependency is required for Claude API dispatch"
            ) from exc

        client = anthropic.Anthropic(api_key=api_key)
        model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-7")
        if skill_ref:
            message = client.beta.messages.create(
                model=model,
                max_tokens=2048,
                betas=["code-execution-2025-08-25", "skills-2025-10-02"],
                container={"skills": [skill_ref]},
                messages=[{"role": "user", "content": prompt}],
                tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
            )
        else:
            message = client.messages.create(
                model=model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
        content_parts = getattr(message, "content", [])
        text_parts: list[str] = []
        for part in content_parts:
            text = getattr(part, "text", None)
            if text:
                text_parts.append(text)
        return {
            "via": "claude_api",
            "content": "\n".join(text_parts).strip(),
            "model": getattr(message, "model", None),
            "skill_ref": skill_ref,
        }


def re_safe_env_key(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value.upper())
