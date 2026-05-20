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


def parse_version(v_str: str) -> tuple[int, int, int]:
    """Parse a semantic version string (e.g. 'v1.2.3', '0.1.0-alpha') into a numeric tuple."""
    if v_str.startswith('v'):
        v_str = v_str[1:]
    parts = []
    for p in v_str.split('.'):
        match = re.match(r'^(\d+)', p)
        if match:
            parts.append(int(match.group(1)))
        else:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return (parts[0], parts[1], parts[2])


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
    schema_path = project_root / "spec" / "agent-schema.json"
    if not schema_path.exists():
        schema_path = project_root / "schemas" / "agent-schema.json"
    if not schema_path.exists():
        logger.warning("agent-schema.json not found in spec/ or schemas/. Schema validation skipped.")
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

    SUPPORTED_PROTOCOL_VERSION = "1.0.0"

    def __init__(self, config_path: str | Path = ".agent/agent.md") -> None:
        self.config_path = Path(config_path)
        self.config = load_agent_config(self.config_path)
        validate_agent_schema(self.config, self.config_path)
        validate_agent_config_paths(self.config, self.config_path)
        self._check_version_compat()
        self.layout = load_agent_layout(self.config, self.config_path)
        
        # Resolve skills directory path
        skills_dir_path = None
        if self.layout and isinstance(self.layout, dict):
            skills_dir_path = self.layout.get("directories", {}).get("skills")
        if not skills_dir_path:
            skills_dir_path = Path(".agent/skills")

        self.router = Router(
            tools=self.config.get("tools", []), 
            mcp_servers=self.config.get("mcp_servers", {}),
            skills_dir=skills_dir_path
        )

        # -- Schema Evolution ------------------------------------------------
        self.schema_evolution_config = self.config.get("schema_evolution", {})

        # -- Memory backend(s) -----------------------------------------------
        from .memory import create_memory_backend

        mem_cfg = self.config.get("memory", {})
        if not isinstance(mem_cfg, dict):
            mem_cfg = {}
        
        mem_path = mem_cfg.get("path")
        self.memory_tiers = {}
        
        # Support both legacy "backend" and new "tiers" schema
        if "tiers" in mem_cfg and isinstance(mem_cfg["tiers"], dict):
            for tier_name, backend_name in mem_cfg["tiers"].items():
                tier_path = mem_path
                if tier_path and backend_name == "sqlite":
                    tier_path = Path(tier_path) / f"{tier_name}.db"
                self.memory_tiers[tier_name] = create_memory_backend(backend_name, path=tier_path)
            
            # For backwards compatibility
            if "persistent" in self.memory_tiers:
                self.memory = self.memory_tiers["persistent"]
            elif "session" in self.memory_tiers:
                self.memory = self.memory_tiers["session"]
            elif self.memory_tiers:
                self.memory = next(iter(self.memory_tiers.values()))
            else:
                self.memory = create_memory_backend("local", path=mem_path)
        else:
            # Legacy fallback
            backend_name = mem_cfg.get("backend", "local")
            self.memory = create_memory_backend(backend_name, path=mem_path)
            self.memory_tiers["persistent"] = self.memory

        # -- Knowledge Base ---------------------------------------------------
        from .knowledge import KnowledgeBase

        self.knowledge_base = KnowledgeBase(self)

        # -- Prompt Composer --------------------------------------------------
        from .prompt_composer import PromptComposer

        self.prompt_composer = PromptComposer(self)


        logger.info(
            "AgentEngine initialised - name=%s version=%s tools=%s memory=%s",
            self.config.get("name"),
            self.config.get("version"),
            self.config.get("tools"),
            type(self.memory).__name__,
        )

    def _check_version_compat(self) -> None:
        """Check compatibility between runtime version and manifest versions, logging warnings if mismatched."""
        from . import __version__ as runtime_version_str
        
        protocol_version_str = self.config.get("protocol_version", "1.0.0")
        min_runtime_version_str = self.config.get("min_runtime_version", "0.1.0")

        # 1. Compare min_runtime_version
        try:
            req_runtime = parse_version(min_runtime_version_str)
            curr_runtime = parse_version(runtime_version_str)
            if curr_runtime < req_runtime:
                logger.warning(
                    "The agent manifest requires minimum runtime version %s, but the current runtime is %s.",
                    min_runtime_version_str,
                    runtime_version_str
                )
        except Exception as e:
            logger.debug("Failed to compare min_runtime_version: %s", e)

        # 2. Compare protocol_version major mismatch
        try:
            req_protocol = parse_version(protocol_version_str)
            supp_protocol = parse_version(self.SUPPORTED_PROTOCOL_VERSION)
            if req_protocol[0] != supp_protocol[0]:
                logger.warning(
                    "The agent manifest uses protocol version %s, but the runtime supports protocol version %s. "
                    "This major version difference may cause unexpected behavior.",
                    protocol_version_str,
                    self.SUPPORTED_PROTOCOL_VERSION
                )
        except Exception as e:
            logger.debug("Failed to compare protocol_version: %s", e)

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

    def execute_workflow(self, workflow_name: str, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        """Load and execute a workflow DAG by its name."""
        from .workflow_engine import WorkflowEngine
        engine = WorkflowEngine(self)
        return engine.run(workflow_name, inputs or {})

    def resume_workflow(
        self,
        workflow_name: str,
        session_id: str,
        step_id: str | None = None,
    ) -> dict[str, Any]:
        """Resume a workflow session from a designated checkpoint step."""
        from .workflow_engine import WorkflowEngine
        engine = WorkflowEngine(self)
        return engine.resume(workflow_name, session_id, step_id)

    def export_handoff(
        self,
        task_state: str,
        pending_steps: list[str],
        context_summary: str,
        memory_keys: list[str] | None = None,
        handoff_id: str | None = None,
    ) -> str:
        """Export the current context, pending tasks, and selected memory snapshot as a handoff packet.

        The packet will be signed with a SHA-256 integrity checksum and stored as a JSON
        contract under the designated handoff directory (.agent/memory/handoff/<handoff_id>.json).

        Parameters
        ----------
        task_state : str
            A description of the current task state.
        pending_steps : list[str]
            A list of pending steps or tasks to be executed by the next agent.
        context_summary : str
            A descriptive summary of context, objectives, and progress so far.
        memory_keys : list[str], optional
            A whitelist of memory keys to snapshot. If None, snapshot all keys.
        handoff_id : str, optional
            A custom handoff identifier. If None, a random UUID v4 will be generated.

        Returns
        -------
        str
            The handoff_id.
        """
        import uuid
        import hashlib
        import json

        if not handoff_id:
            handoff_id = str(uuid.uuid4())

        # Resolve memory snapshot
        memory_snapshot = {}
        if memory_keys is not None:
            for k in memory_keys:
                val = self.memory.read(k)
                if val is not None:
                    memory_snapshot[k] = val
        else:
            # If no keys specified, read all keys
            for k in self.memory.list_keys():
                val = self.memory.read(k)
                if val is not None:
                    memory_snapshot[k] = val

        # Construct packet
        packet = {
            "task_state": task_state,
            "pending_steps": pending_steps,
            "context_summary": context_summary,
            "memory_snapshot": memory_snapshot,
        }

        # Calculate integrity checksum
        canonical = json.dumps(packet, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        packet["checksum"] = checksum

        # Validate against schema if jsonschema is available
        schema_path = self.config_path.parent.parent / "spec" / "memory.schema.json"
        if schema_path.exists():
            try:
                import jsonschema
                with schema_path.open(encoding="utf-8") as f:
                    schema = json.load(f)
                jsonschema.validate(instance={"handoff": packet}, schema=schema)
            except ImportError:
                pass
            except Exception as e:
                logger.warning("Handoff packet failed schema validation before export: %s", e)

        # Resolve handoff directory
        handoff_dir = None
        if isinstance(self.layout, dict):
            mem_dir = self.layout.get("directories", {}).get("memory")
            if mem_dir:
                handoff_dir = Path(mem_dir) / "handoff"
        if handoff_dir is None:
            handoff_dir = self.config_path.parent / "memory" / "handoff"

        handoff_dir = Path(handoff_dir)
        handoff_dir.mkdir(parents=True, exist_ok=True)

        dest_file = handoff_dir / f"{handoff_id}.json"
        try:
            dest_file.write_text(json.dumps(packet, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info("Exported handoff packet to %s", dest_file)
        except OSError as e:
            raise OSError(f"Failed to write handoff packet to {dest_file}: {e}") from e

        return handoff_id

    def import_handoff(self, handoff_id: str) -> dict[str, Any]:
        """Import, verify, and restore state from a designated handoff packet.

        The handoff packet's integrity checksum is validated, and the memory snapshot
        is restored into the current memory backend.

        Parameters
        ----------
        handoff_id : str
            The identifier of the handoff to import.

        Returns
        -------
        dict[str, Any]
            The imported handoff packet structure.
        """
        import hashlib
        import json

        # Resolve handoff directory
        handoff_dir = None
        if isinstance(self.layout, dict):
            mem_dir = self.layout.get("directories", {}).get("memory")
            if mem_dir:
                handoff_dir = Path(mem_dir) / "handoff"
        if handoff_dir is None:
            handoff_dir = self.config_path.parent / "memory" / "handoff"

        handoff_dir = Path(handoff_dir)
        src_file = handoff_dir / f"{handoff_id}.json"

        if not src_file.exists():
            # Fall back to root directory relative check
            project_root = self.config_path.parent.parent
            src_file_alt = project_root / ".agent" / "memory" / "handoff" / f"{handoff_id}.json"
            if src_file_alt.exists():
                src_file = src_file_alt
            else:
                raise FileNotFoundError(f"Handoff file not found at: {src_file}")

        try:
            packet = json.loads(src_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise ValueError(f"Failed to read/parse handoff JSON: {e}") from e

        # Extract and verify checksum
        checksum = packet.pop("checksum", None)
        if not checksum:
            raise ValueError("Integrity verification failed: missing checksum in handoff packet.")

        canonical = json.dumps(packet, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        expected_checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        if checksum != expected_checksum:
            raise ValueError(
                f"Handoff packet integrity check failed! Mismatch:\n"
                f"  Expected: {expected_checksum}\n"
                f"  Got:      {checksum}"
            )

        # Validate schema
        schema_path = self.config_path.parent.parent / "spec" / "memory.schema.json"
        if schema_path.exists():
            try:
                import jsonschema
                with schema_path.open(encoding="utf-8") as f:
                    schema = json.load(f)
                packet_to_validate = dict(packet)
                packet_to_validate["checksum"] = checksum
                jsonschema.validate(instance={"handoff": packet_to_validate}, schema=schema)
            except ImportError:
                pass
            except Exception as e:
                raise ValueError(f"Handoff packet failed schema validation on import: {e}") from e

        # Restore memory snapshot
        memory_snapshot = packet.get("memory_snapshot", {})
        for k, v in memory_snapshot.items():
            self.memory.write(k, v)

        # Re-inject checksum back to return packet
        packet["checksum"] = checksum

        logger.info("Successfully imported handoff state from %s", src_file)
        return packet

