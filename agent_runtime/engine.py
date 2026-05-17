"""Core engine — loads .agent/agent.md config and orchestrates routing."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .logger import get_logger
from .router import Router

logger = get_logger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def load_agent_config(agent_md: str | Path = ".agent/agent.md") -> dict[str, Any]:
    """Parse YAML front-matter from *agent_md* and return it as a dict."""
    path = Path(agent_md)
    if not path.exists():
        raise FileNotFoundError(f"Agent config not found: {path}")

    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"No YAML front-matter found in {path}")

    config: dict[str, Any] = yaml.safe_load(match.group(1)) or {}
    logger.debug("Loaded agent config from %s: %s", path, config)
    return config


class AgentEngine:
    """Bootstraps the agent runtime from the protocol config."""

    def __init__(self, config_path: str | Path = ".agent/agent.md") -> None:
        self.config = load_agent_config(config_path)
        self.router = Router(tools=self.config.get("tools", []))
        logger.info(
            "AgentEngine initialised — name=%s version=%s tools=%s",
            self.config.get("name"),
            self.config.get("version"),
            self.config.get("tools"),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, tool: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Dispatch *params* to *tool* via the router and return the result."""
        params = params or {}
        logger.info("Engine dispatching — tool=%s params=%s", tool, params)
        result = self.router.route(tool, params)
        logger.info("Engine result — tool=%s result=%s", tool, result)
        return result
