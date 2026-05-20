"""Prompt Composer module for the Portable Agent Protocol.

Manages loading, validating, and building prompt templates with strict
prompt injection defense for system prompts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from .logger import get_logger

if TYPE_CHECKING:
    from .engine import AgentEngine

logger = get_logger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_HEADER_RE = re.compile(r"^##\s+([a-zA-Z0-9_-]+)", re.MULTILINE)
_CODEBLOCK_RE = re.compile(r"```[a-zA-Z0-9_-]*\n(.*?)\n```", re.DOTALL)


class SafePromptString(str):
    """Marker class for validated and trusted prompt strings.

    Variables of this type bypass prompt injection security validation.
    """
    pass


def validate_prompt_string(value: str) -> SafePromptString:
    """Scan a string for potential prompt injection vectors.

    Raises ValueError if a dangerous pattern is detected. Otherwise, returns
    a SafePromptString instance wrapping the value.
    """
    if not isinstance(value, str):
        return SafePromptString(str(value))

    # Common prompt injection patterns (case-insensitive)
    dangerous_patterns = [
        r"ignore.*\binstructions?\b",
        r"you\s+are\s+now\s+a",
        r"system\s+override",
        r"override\s+system",
        r"do\s+not\s+follow",
        r"instead\s+of\s+following",
        r"ignore.*\bprompt\b",
        r"new\s+instructions\b",
        r"assistant:",
        r"user:",
        r"system:"
    ]

    val_lower = value.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, val_lower):
            raise ValueError(
                f"Potential prompt injection detected. Content matched pattern: '{pattern}'"
            )

    return SafePromptString(value)


class PromptComposer:
    """Manages prompt template indexing, verification, and rendering.

    Parameters
    ----------
    engine : AgentEngine
        The parent engine used to resolve layouts and schema paths.
    """

    def __init__(self, engine: AgentEngine) -> None:
        self._engine = engine

        # Resolve paths
        layout = getattr(engine, "layout", None)
        prompts_file: Path | None = None
        prompts_dir: Path | None = None

        if isinstance(layout, dict):
            prompts_file = layout.get("entrypoints", {}).get("prompts")
            prompts_dir = layout.get("directories", {}).get("prompts")

        if prompts_file is None:
            prompts_file = engine.config_path.parent / "prompts.md"
        if prompts_dir is None:
            prompts_dir = engine.config_path.parent / "prompts"

        self._prompts_file = Path(prompts_file)
        self._prompts_dir = Path(prompts_dir)
        self._prompts: dict[str, dict[str, Any]] = {}

        # Load Schema if available
        self._schema: dict[str, Any] | None = None
        schema_path = engine.config_path.parent.parent / "spec" / "prompt.schema.json"
        if schema_path.exists():
            try:
                self._schema = json.loads(schema_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Failed to load prompt schema: %s", e)

        # Load all prompt templates
        self._load_prompts_file()
        self._load_prompts_directory()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, prompt_id: str) -> dict[str, Any] | None:
        """Return the parsed prompt contract for *prompt_id*, or None."""
        return self._prompts.get(prompt_id)

    def list_prompts(self) -> list[dict[str, Any]]:
        """Return metadata for all indexed prompts."""
        return list(self._prompts.values())

    def build(self, prompt_id: str, variables: dict[str, Any] | None = None) -> str:
        """Interpolate variables into the prompt template for *prompt_id*.

        Performs strict prompt injection checks on all variable values if building
        a system prompt.
        """
        prompt = self.get(prompt_id)
        if not prompt:
            raise KeyError(f"Prompt '{prompt_id}' not found.")

        vars_dict = variables or {}
        req_vars = prompt.get("variables", [])

        # Check for missing variables
        missing = [v for v in req_vars if v not in vars_dict]
        if missing:
            raise ValueError(
                f"Missing required variables for prompt '{prompt_id}': {', '.join(missing)}"
            )

        # Build actual values dict, casting/checking as necessary
        interpolated_vars: dict[str, str] = {}
        is_system = "system" in prompt_id.lower() or "role" in prompt_id.lower()

        for k in req_vars:
            val = vars_dict[k]
            val_str = str(val)

            # Security validation for system/role prompts
            if is_system:
                if not isinstance(val, SafePromptString):
                    validate_prompt_string(val_str)

            interpolated_vars[k] = val_str

        try:
            return prompt["template"].format(**interpolated_vars)
        except KeyError as e:
            raise ValueError(f"Variables mismatch during formatting: missing {e}")

    # ------------------------------------------------------------------
    # Loading / Parsing Logic
    # ------------------------------------------------------------------

    def _load_prompts_file(self) -> None:
        """Parse templates out of prompts.md catalog."""
        if not self._prompts_file.exists():
            logger.debug("Prompts catalog file does not exist: %s", self._prompts_file)
            return

        try:
            content = self._prompts_file.read_text(encoding="utf-8")
        except OSError as e:
            logger.warning("Failed to read prompts file: %s", e)
            return

        # Simple markdown section parser
        sections = content.split("\n## ")
        for i, section in enumerate(sections):
            if i == 0:
                # Introduction text, skip
                continue

            lines = section.splitlines()
            if not lines:
                continue

            header = lines[0].strip()
            # Extract id
            prompt_id_match = re.match(r"^([a-zA-Z0-9_-]+)", header)
            if not prompt_id_match:
                continue
            prompt_id = prompt_id_match.group(1)

            body = "\n".join(lines[1:])
            # Extract first text codeblock
            code_match = _CODEBLOCK_RE.search(body)
            if not code_match:
                continue
            template = code_match.group(1).strip("\r\n")

            # Extract variables automatically using regex
            variables = re.findall(r"\{([a-zA-Z0-9_-]+)\}", template)
            # Deduplicate variables while preserving order
            seen = set()
            deduped_vars = [v for v in variables if not (v in seen or seen.add(v))]

            prompt_dict = {
                "id": prompt_id,
                "version": "1.0.0",
                "usage": f"Parsed from prompts catalog ({self._prompts_file.name})",
                "variables": deduped_vars,
                "template": template,
            }

            # Validate against schema if available
            self._validate_and_register(prompt_dict)

    def _load_prompts_directory(self) -> None:
        """Parse individual *.md templates from prompts directory."""
        if not self._prompts_dir.exists():
            logger.debug("Prompts directory does not exist: %s", self._prompts_dir)
            return

        for path in self._prompts_dir.glob("*.md"):
            if path.name == "__init__.md":
                continue

            try:
                text = path.read_text(encoding="utf-8")
            except OSError as e:
                logger.warning("Failed to read prompt file %s: %s", path.name, e)
                continue

            match = _FRONTMATTER_RE.match(text)
            if not match:
                logger.warning("Prompt contract %s missing YAML front-matter", path.name)
                continue

            try:
                metadata = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError as e:
                logger.warning("YAML parse error in prompt %s: %s", path.name, e)
                continue

            # Template is the markdown body
            body = text[match.end():].strip()

            prompt_dict = {
                "id": metadata.get("id", path.stem),
                "version": metadata.get("version", "1.0.0"),
                "usage": metadata.get("usage", ""),
                "variables": metadata.get("variables", []),
                "template": body,
            }

            # Validate against schema if available
            self._validate_and_register(prompt_dict)

    def _validate_and_register(self, prompt_dict: dict[str, Any]) -> None:
        """Validate a prompt dictionary against schema and store in registry."""
        if self._schema:
            try:
                import jsonschema
                jsonschema.validate(instance=prompt_dict, schema=self._schema)
            except ImportError:
                # jsonschema not installed, skip validation
                pass
            except Exception as e:
                logger.warning(
                    "Prompt '%s' failed schema validation: %s",
                    prompt_dict.get("id"),
                    e,
                )
                return

        self._prompts[prompt_dict["id"]] = prompt_dict
