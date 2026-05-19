"""Convert PAP skill contracts to and from Anthropic SKILL.md files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_HEADING_RE = re.compile(r"^#\s*(?:Skill:\s*)?(.+?)\s*$", re.MULTILINE | re.IGNORECASE)


def _slug_name(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().replace("_", "-")).strip("-")
    return (slug.lower() or "skill")[:64].strip("-") or "skill"


def _pap_name(name: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip().replace("-", "_")).strip("_")
    return clean.lower() or "skill"


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    metadata: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata, text[match.end() :]


def _extract_pap_metadata(path: Path, text: str) -> tuple[str, str, str]:
    metadata, body = _parse_frontmatter(text)
    name = metadata.get("skill") or metadata.get("name")

    if not name:
        heading = _HEADING_RE.search(body)
        if heading:
            name = heading.group(1).strip()
    if not name:
        name = path.stem

    description = metadata.get("description", "").strip()
    if not description:
        description = _first_plain_paragraph(body)
    if not description:
        description = f"PAP skill contract for {name}."

    return _pap_name(name), description, body.strip()


def _first_plain_paragraph(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("- ") or line.startswith("`"):
            if lines:
                break
            continue
        lines.append(line)
    return " ".join(lines).strip()


def _yaml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _anthropic_description(value: str) -> str:
    clean = value.replace("<", "").replace(">", "").strip()
    if len(clean) > 1024:
        clean = clean[:1021].rstrip() + "..."
    return clean or "PAP skill contract."


def _metadata_errors(name: str, description: str) -> list[str]:
    errors: list[str] = []
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        errors.append("name must be 1-64 lowercase letters, numbers, or hyphens")
    if name in {"anthropic", "claude"}:
        errors.append("name must not use a reserved Anthropic skill word")
    if not description:
        errors.append("description must be non-empty")
    if len(description) > 1024:
        errors.append("description must be 1024 characters or fewer")
    if "<" in description or ">" in description:
        errors.append("description must not contain XML-like angle brackets")
    return errors


def pap_to_anthropic(pap_skill_path: Path) -> str:
    """Convert a PAP skill contract markdown file to Anthropic SKILL.md text."""
    path = Path(pap_skill_path)
    text = path.read_text(encoding="utf-8")
    name, description, body = _extract_pap_metadata(path, text)
    anthropic_name = _slug_name(name)
    description = _anthropic_description(description)
    title = anthropic_name.replace("-", " ").title()

    if not body:
        body = f"# Skill: {name}\n\n{description}"

    return (
        "---\n"
        f"name: {_yaml_string(anthropic_name)}\n"
        f"description: {_yaml_string(description)}\n"
        "---\n\n"
        f"# {title} Skill\n\n"
        "This skill was exported from a Portable Agent Protocol contract.\n\n"
        "## PAP Contract\n\n"
        f"{body}\n"
    )


def anthropic_to_pap(skill_md_path: Path) -> str:
    """Convert an Anthropic SKILL.md file to PAP skill contract markdown text."""
    path = Path(skill_md_path)
    text = path.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(text)
    name = _pap_name(metadata.get("name") or path.parent.name or path.stem)
    description = metadata.get("description") or _first_plain_paragraph(body)
    description = description or f"Anthropic-compatible skill contract for {name}."

    return (
        f"# Skill: {name}\n\n"
        "## Description\n\n"
        f"{description}\n\n"
        "## Source Compatibility\n\n"
        "- source: anthropic\n"
        "- anthropic_compatible: true\n\n"
        "## Instructions\n\n"
        f"{body.strip()}\n"
    )


def export_all_skills(agent_dir: Path, output_dir: Path) -> list[Path]:
    """Export every PAP skill contract in ``agent_dir`` to Anthropic format."""
    agent_path = Path(agent_dir)
    if agent_path.name != ".agent" and (agent_path / ".agent").exists():
        agent_path = agent_path / ".agent"

    skills_dir = agent_path / "skills"
    if not skills_dir.exists():
        raise FileNotFoundError(f"PAP skills directory not found: {skills_dir}")

    output_path = Path(output_dir)
    exported: list[Path] = []

    for pap_skill in sorted(skills_dir.glob("*.md")):
        if pap_skill.stem.startswith("_") or pap_skill.stem == "__init__":
            continue
        name, _, _ = _extract_pap_metadata(pap_skill, pap_skill.read_text(encoding="utf-8"))
        skill_dir = output_path / _slug_name(name)
        skill_dir.mkdir(parents=True, exist_ok=True)
        target = skill_dir / "SKILL.md"
        target.write_text(pap_to_anthropic(pap_skill), encoding="utf-8")
        exported.append(target)

    return exported


def validate_compatibility(agent_dir: Path) -> list[dict[str, Any]]:
    """Validate local PAP skills for Anthropic SKILL.md export compatibility."""
    agent_path = Path(agent_dir)
    if agent_path.name != ".agent" and (agent_path / ".agent").exists():
        agent_path = agent_path / ".agent"

    skills_dir = agent_path / "skills"
    if not skills_dir.exists():
        raise FileNotFoundError(f"PAP skills directory not found: {skills_dir}")

    reports: list[dict[str, Any]] = []
    for pap_skill in sorted(skills_dir.glob("*.md")):
        if pap_skill.stem.startswith("_") or pap_skill.stem == "__init__":
            continue
        errors: list[str] = []
        name = pap_skill.stem
        anthropic_name = _slug_name(name)
        try:
            exported = pap_to_anthropic(pap_skill)
            metadata, body = _parse_frontmatter(exported)
            if not metadata.get("name"):
                errors.append("missing Anthropic frontmatter name")
            if not metadata.get("description"):
                errors.append("missing Anthropic frontmatter description")
            errors.extend(
                _metadata_errors(
                    metadata.get("name", ""),
                    metadata.get("description", ""),
                )
            )
            if not body.strip():
                errors.append("missing instruction body")
        except Exception as exc:
            errors.append(str(exc))
        reports.append(
            {
                "name": name,
                "pap_contract_path": str(pap_skill),
                "anthropic_skill_path": f"./anthropic_skills/{anthropic_name}/SKILL.md",
                "anthropic_compatible": not errors,
                "errors": errors,
            }
        )
    return reports
