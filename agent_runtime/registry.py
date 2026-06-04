"""Portable Agent Protocol registry operations for installing and publishing skills."""

from __future__ import annotations

import json
import os
import shutil
import urllib.request
from pathlib import Path
from typing import Any

from .logger import get_logger
from .lint import parse_front_matter

logger = get_logger(__name__)

# Default local fallback registry directory
DEFAULT_REGISTRY_DIR = Path("registry")


def get_registry_url() -> str | None:
    """Return the remote registry base URL if configured via env var."""
    return os.environ.get("PAP_REGISTRY_URL")


def validate_skill_contract(contract_path: Path | str) -> dict[str, Any]:
    """Validate a skill contract against spec/skill-contract.schema.json and custom business rules.

    Raises ValueError if validation fails.
    """
    path = Path(contract_path)
    if not path.exists():
        raise FileNotFoundError(f"Contract file not found at: {path}")

    content = path.read_text(encoding="utf-8")
    data, err = parse_front_matter(content)
    if err:
        raise ValueError(f"Front-matter parsing error: {err}")
    if not data:
        raise ValueError("Missing or invalid YAML front-matter.")

    # 1. JSON Schema validation
    project_root = Path(__file__).parent.parent
    schema_path = project_root / "spec" / "skill-contract.schema.json"
    if not schema_path.exists():
        schema_path = project_root / "schemas" / "skill-contract.schema.json"

    if schema_path.exists():
        try:
            import jsonschema
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.validate(instance=data, schema=schema)
        except ImportError:
            # Fallback manual validation if jsonschema is not installed
            logger.debug("jsonschema package not installed, running basic manual validation")
            _manual_schema_validation(data)
        except Exception as ve:
            raise ValueError(f"Schema validation failed: {ve}")
    else:
        _manual_schema_validation(data)

    # 2. Assert custom strict business rules (matching test_skill_contracts.py)
    # Rule A: id and name must be present and identical
    skill_id = data.get("id")
    name = data.get("name")
    if not skill_id or not name:
        raise ValueError("Contract is missing 'id' or 'name'")
    if skill_id != name:
        raise ValueError(f"Contract 'id' ({skill_id}) must be identical to 'name' ({name})")

    # Rule B: version must match semver pattern
    version = data.get("version")
    if not version:
        raise ValueError("Contract is missing 'version'")
    import re
    if not re.match(r"^\d+\.\d+\.\d+$", str(version)):
        raise ValueError(f"Version '{version}' is not a valid semver pattern")

    # Rule C: inputs validation
    inputs = data.get("inputs")
    if not isinstance(inputs, dict):
        raise ValueError("'inputs' must be an object")
    for param_name, param_info in inputs.items():
        if not isinstance(param_info, dict) or "type" not in param_info or "description" not in param_info:
            raise ValueError(f"Input parameter '{param_name}' must declare 'type' and 'description'")

    # Rule D: outputs validation
    outputs = data.get("outputs")
    if not isinstance(outputs, dict):
        raise ValueError("'outputs' must be an object")
    for output_name, output_info in outputs.items():
        if not isinstance(output_info, dict) or "type" not in output_info or "description" not in output_info:
            raise ValueError(f"Output field '{output_name}' must declare 'type' and 'description'")

    # Rule E: safety_notes validation
    safety_notes = data.get("safety_notes")
    if not isinstance(safety_notes, list) or len(safety_notes) == 0:
        raise ValueError("'safety_notes' must be a list containing at least one constraint")

    # Rule F: vendor anonymization check
    forbidden_terms = ["anthropic", "claude", "openai", "gpt-4", "gpt-3", "gemini", "vertex", "langchain"]
    content_lower = content.lower()
    for term in forbidden_terms:
        if term in content_lower:
            raise ValueError(f"Forbidden vendor-specific term '{term}' found in skill contract")

    return data


def _manual_schema_validation(data: dict[str, Any]) -> None:
    required = ["id", "name", "description", "version", "inputs", "outputs", "safety_notes"]
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required contract field: '{field}'")


def install_skill(
    skill_id: str,
    skills_dir: Path | str,
    registry_dir: Path | str = DEFAULT_REGISTRY_DIR,
) -> dict[str, Any]:
    """Fetch and install a skill contract from the registry.

    Supports remote URL registry via PAP_REGISTRY_URL env var, or local static registry directory fallback.
    """
    skills_dir = Path(skills_dir)
    skills_dir.mkdir(parents=True, exist_ok=True)
    registry_url = get_registry_url()

    # 1. Fetch Registry Index
    if registry_url:
        index_url = f"{registry_url.rstrip('/')}/index.json"
        try:
            logger.info("Fetching registry index from remote URL: %s", index_url)
            with urllib.request.urlopen(index_url, timeout=5) as response:
                index_data = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Failed to fetch registry index from {index_url}: {e}") from e
    else:
        registry_path = Path(registry_dir)
        index_path = registry_path / "index.json"
        if not index_path.exists():
            raise FileNotFoundError(f"Registry index file not found at: {index_path}")
        try:
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to parse registry index JSON: {e}") from e

    # 2. Resolve skill entry in index
    skills_index = index_data.get("skills", {})
    if skill_id not in skills_index:
        raise KeyError(f"Skill '{skill_id}' not found in the registry index.")

    skill_entry = skills_index[skill_id]
    rel_path = skill_entry.get("path")
    if not rel_path:
        raise ValueError(f"Registry index entry for '{skill_id}' is missing file path.")

    dest_contract_path = skills_dir / f"{skill_id}.md"

    # 3. Fetch/Copy contract content
    if registry_url:
        contract_url = f"{registry_url.rstrip('/')}/{rel_path}"
        try:
            logger.info("Fetching skill contract from remote URL: %s", contract_url)
            with urllib.request.urlopen(contract_url, timeout=5) as response:
                content = response.read().decode("utf-8")
            dest_contract_path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise RuntimeError(f"Failed to download skill contract from {contract_url}: {e}") from e
    else:
        src_contract_path = Path(registry_dir) / rel_path
        if not src_contract_path.exists():
            raise FileNotFoundError(f"Registry skill contract file not found at: {src_contract_path}")
        shutil.copy2(src_contract_path, dest_contract_path)

    # 4. Perform sanity check post-installation
    try:
        validate_skill_contract(dest_contract_path)
    except Exception as e:
        # Cleanup if validation failed
        if dest_contract_path.exists():
            dest_contract_path.unlink()
        raise ValueError(f"Installed skill failed validation: {e}") from e

    return skill_entry


def publish_skill(
    contract_path: Path | str,
    registry_dir: Path | str = DEFAULT_REGISTRY_DIR,
) -> dict[str, Any]:
    """Validate and publish a skill contract to the local registry database.

    Updates the registry index and moves/writes the contract file under registry/skills/.
    """
    contract_path = Path(contract_path)
    registry_path = Path(registry_dir)
    registry_skills_dir = registry_path / "skills"

    # 1. Validate contract file
    metadata = validate_skill_contract(contract_path)
    skill_id = metadata["id"]

    # 2. Write to registry skills directory
    registry_skills_dir.mkdir(parents=True, exist_ok=True)
    dest_path = registry_skills_dir / f"{skill_id}.md"
    shutil.copy2(contract_path, dest_path)

    # 3. Read & Update index
    index_path = registry_path / "index.json"
    if index_path.exists():
        try:
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
        except Exception:
            index_data = {"registry_version": "1.0.0", "skills": {}}
    else:
        index_data = {"registry_version": "1.0.0", "skills": {}}

    skills_index = index_data.setdefault("skills", {})
    skill_entry = {
        "id": skill_id,
        "name": metadata.get("name", skill_id),
        "version": metadata.get("version", "1.0.0"),
        "description": metadata.get("description", ""),
        "author": metadata.get("author", "anonymous"),
        "path": f"skills/{skill_id}.md"
    }
    skills_index[skill_id] = skill_entry

    # 4. Validate updated index against registry-schema
    project_root = registry_path.parent
    registry_schema_path = project_root / "spec" / "registry-schema.json"
    if registry_schema_path.exists():
        try:
            import jsonschema
            schema = json.loads(registry_schema_path.read_text(encoding="utf-8"))
            jsonschema.validate(instance=index_data, schema=schema)
        except ImportError:
            pass

    # Save index
    index_path.write_text(json.dumps(index_data, indent=2, ensure_ascii=False), encoding="utf-8")

    return skill_entry
