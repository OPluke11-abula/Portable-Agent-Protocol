"""Core engine that loads .agent/agent.md config and orchestrates routing."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

try:
    import jsonschema
except ImportError:
    jsonschema = None

from .logger import get_logger
from .router import Router

logger = get_logger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def load_agent_config(agent_md: str | Path = ".agent/agent.md") -> dict[str, Any]:
    """Parse YAML front matter from *agent_md* and return it as a dict."""
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


def _project_root_from_config(config_path: Path) -> Path:
    """Infer the project root from a config path."""
    if config_path.parent.name == ".agent":
        return config_path.parent.parent
    return config_path.parent


def _resolve_declared_path(raw_path: str, config_path: Path) -> Path:
    """Resolve a declared protocol path against the project or config dir."""
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate

    project_root = _project_root_from_config(config_path)
    config_dir = config_path.parent

    project_relative = project_root / candidate
    config_relative = config_dir / candidate

    if project_relative.exists():
        return project_relative
    if config_relative.exists():
        return config_relative
    return project_relative


def _iter_declared_paths(config: dict[str, Any]) -> list[tuple[str, str]]:
    """Return known path-like fields declared in the agent config."""
    declared: list[tuple[str, str]] = []

    for section_name in ("memory", "prompts", "workflows"):
        section = config.get(section_name)
        if isinstance(section, dict):
            value = section.get("path")
            if isinstance(value, str):
                declared.append((f"{section_name}.path", value))

    protocol = config.get("protocol")
    if not isinstance(protocol, dict):
        return declared

    for key in ("root", "manifest"):
        value = protocol.get(key)
        if isinstance(value, str):
            declared.append((f"protocol.{key}", value))

    for group_name in ("entrypoints", "directories"):
        group = protocol.get(group_name)
        if not isinstance(group, dict):
            continue
        for name, value in group.items():
            if isinstance(value, str):
                declared.append((f"protocol.{group_name}.{name}", value))

    return declared


def validate_agent_schema(config: dict[str, Any], config_path: Path) -> None:
    """Validate the agent config against the JSON schema."""
    if jsonschema is None:
        logger.warning("jsonschema is not installed. Schema validation skipped.")
        return
        
    project_root = _project_root_from_config(config_path)
    schema_path = project_root / "schemas" / "agent-schema.json"
    if not schema_path.exists():
        logger.warning("agent-schema.json not found at %s. Schema validation skipped.", schema_path)
        return
        
    try:
        with schema_path.open(encoding="utf-8") as f:
            schema = json.load(f)
        jsonschema.validate(instance=config, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValueError(f"Schema validation failed: {e.message}") from e
    except json.JSONDecodeError as e:
        logger.error("Failed to parse agent-schema.json: %s", e)


def validate_agent_workspace(config_path: str | Path = ".agent/agent.md") -> None:
    """Validate the agent workspace schema and paths."""
    config_path = Path(config_path)
    config = load_agent_config(config_path)
    validate_agent_schema(config, config_path)
    validate_agent_config_paths(config, config_path)


def validate_agent_config_paths(
    config: dict[str, Any], agent_md: str | Path = ".agent/agent.md"
) -> None:
    """Validate that declared protocol paths exist."""
    config_path = Path(agent_md)

    for label, raw_path in _iter_declared_paths(config):
        resolved = _resolve_declared_path(raw_path, config_path)
        if not resolved.exists():
            raise FileNotFoundError(
                f"Declared path '{label}' does not exist: {raw_path} "
                f"(resolved to {resolved})"
            )

    protocol = config.get("protocol")
    if not isinstance(protocol, dict):
        return

    directories = protocol.get("directories")
    if not isinstance(directories, dict):
        return

    skills_dir_raw = directories.get("skills")
    if not isinstance(skills_dir_raw, str):
        return

    skills_dir = _resolve_declared_path(skills_dir_raw, config_path)
    tools = config.get("tools")
    if not isinstance(tools, list):
        return

    for tool_name in tools:
        if not isinstance(tool_name, str):
            continue
        skill_spec = skills_dir / f"{tool_name}.md"
        if not skill_spec.exists():
            raise FileNotFoundError(
                f"Missing skill spec for tool '{tool_name}': {skill_spec}"
            )


def _iter_markdown_documents(directory: Path) -> list[Path]:
    """Return direct Markdown documents in a declared protocol directory."""
    if not directory.exists() or not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() == ".md"
    )


def load_agent_layout(
    config: dict[str, Any], agent_md: str | Path = ".agent/agent.md"
) -> dict[str, Any]:
    """Resolve the manifest-declared protocol layout.

    The returned layout keeps the top-level entry documents and detailed
    directory documents separate, matching the three-layer .agent contract.
    """
    config_path = Path(agent_md)
    protocol = config.get("protocol")
    if not isinstance(protocol, dict):
        return {
            "root": None,
            "manifest": None,
            "entrypoints": {},
            "directories": {},
            "directory_documents": {},
        }

    root = None
    raw_root = protocol.get("root")
    if isinstance(raw_root, str):
        root = _resolve_declared_path(raw_root, config_path)

    manifest = None
    raw_manifest = protocol.get("manifest")
    if isinstance(raw_manifest, str):
        manifest = _resolve_declared_path(raw_manifest, config_path)

    entrypoints: dict[str, Path] = {}
    raw_entrypoints = protocol.get("entrypoints")
    if isinstance(raw_entrypoints, dict):
        for name, raw_path in raw_entrypoints.items():
            if isinstance(raw_path, str):
                entrypoints[name] = _resolve_declared_path(raw_path, config_path)

    directories: dict[str, Path] = {}
    directory_documents: dict[str, list[Path]] = {}
    raw_directories = protocol.get("directories")
    if isinstance(raw_directories, dict):
        for name, raw_path in raw_directories.items():
            if not isinstance(raw_path, str):
                continue
            directory = _resolve_declared_path(raw_path, config_path)
            directories[name] = directory
            directory_documents[name] = _iter_markdown_documents(directory)

    return {
        "root": root,
        "manifest": manifest,
        "entrypoints": entrypoints,
        "directories": directories,
        "directory_documents": directory_documents,
    }


class AgentEngine:
    """Bootstraps the agent runtime from the protocol config."""

    def __init__(self, config_path: str | Path = ".agent/agent.md") -> None:
        self.config_path = Path(config_path)
        self.config = load_agent_config(self.config_path)
        validate_agent_schema(self.config, self.config_path)
        validate_agent_config_paths(self.config, self.config_path)
        self.layout = load_agent_layout(self.config, self.config_path)
        self.router = Router(
            tools=self.config.get("tools", []), 
            mcp_servers=self.config.get("mcp_servers", {})
        )
        logger.info(
            "AgentEngine initialised - name=%s version=%s tools=%s",
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
        logger.info("Engine dispatching - tool=%s params=%s", tool, params)
        result = self.router.route(tool, params)
        logger.info("Engine result - tool=%s result=%s", tool, result)
        return result
