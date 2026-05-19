"""Load Anthropic skill folders and sync them into the PAP registry."""

from __future__ import annotations

import json
import re
import ssl
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agent_runtime.bridges.anthropic_skill_bridge import anthropic_to_pap


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


@dataclass
class SkillRecord:
    name: str
    description: str
    source: str
    source_path: str
    anthropic_compatible: bool
    pap_contract_path: str | None


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


def _description_from_body(body: str) -> str:
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and not line.startswith("- "):
            return line
    return ""


def _record_from_skill_md(path: Path, source_path: str | None = None) -> SkillRecord:
    text = path.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(text)
    raw_name = metadata.get("name") or path.parent.name or path.stem
    name = _pap_name(raw_name)
    description = metadata.get("description") or _description_from_body(body)
    if not description:
        description = f"Anthropic-compatible skill {name}."
    return SkillRecord(
        name=name,
        description=description,
        source="anthropic",
        source_path=source_path or str(path),
        anthropic_compatible=True,
        pap_contract_path=None,
    )


def load_from_local(skills_dir: Path) -> list[SkillRecord]:
    """Load all Anthropic SKILL.md files from a local skills directory."""
    root = Path(skills_dir)
    if not root.exists():
        raise FileNotFoundError(f"Anthropic skills directory not found: {root}")

    records: list[SkillRecord] = []
    for skill_md in sorted(root.rglob("SKILL.md")):
        if "template" in {part.lower() for part in skill_md.parts}:
            continue
        records.append(_record_from_skill_md(skill_md))
    return records


def _fetch_json(url: str) -> dict:
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "portable-agent"})
    with urlopen(request, timeout=20, context=_ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "portable-agent"})
    with urlopen(request, timeout=20, context=_ssl_context()) as response:
        return response.read().decode("utf-8")


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def load_from_github(repo: str = "anthropics/skills", ref: str = "main") -> list[SkillRecord]:
    """Load Anthropic SKILL.md files from GitHub raw content without cloning."""
    tree_url = f"https://api.github.com/repos/{repo}/git/trees/{ref}?recursive=1"
    try:
        tree = _fetch_json(tree_url)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not load GitHub skill tree for {repo}@{ref}: {exc}") from exc

    records: list[SkillRecord] = []
    for item in tree.get("tree", []):
        path = item.get("path", "")
        if item.get("type") != "blob" or not path.startswith("skills/") or not path.endswith("SKILL.md"):
            continue
        raw_url = f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"
        try:
            text = _fetch_text(raw_url)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"Could not load {raw_url}: {exc}") from exc
        tmp_path = Path(path)
        metadata, body = _parse_frontmatter(text)
        raw_name = metadata.get("name") or tmp_path.parent.name or tmp_path.stem
        description = metadata.get("description") or _description_from_body(body)
        records.append(
            SkillRecord(
                name=_pap_name(raw_name),
                description=description or f"Anthropic-compatible skill {_pap_name(raw_name)}.",
                source="anthropic",
                source_path=raw_url,
                anthropic_compatible=True,
                pap_contract_path=None,
            )
        )
    return records


def _local_pap_records(agent_dir: Path) -> list[SkillRecord]:
    skills_dir = agent_dir / "skills"
    records: list[SkillRecord] = []
    if not skills_dir.exists():
        return records
    for skill_md in sorted(skills_dir.glob("*.md")):
        if skill_md.stem.startswith("_") or skill_md.stem == "__init__":
            continue
        name = _pap_name(skill_md.stem)
        records.append(
            SkillRecord(
                name=name,
                description=f"Local PAP runtime skill {name}.",
                source="pap",
                source_path=f"agent_runtime/tools/{name}.py",
                anthropic_compatible=True,
                pap_contract_path=f".agent/skills/{name}.md",
            )
        )
    return records


def _render_registry(records: list[SkillRecord]) -> str:
    lines = [
        "# Skills Entry Point",
        "",
        "This file is the runtime-facing skill registry for the Portable Agent.",
        "",
        "Use it to map tool names to Python modules or external Anthropic skill",
        "sources. Detailed per-skill PAP contracts live in `.agent/skills/*.md`.",
        "",
        "## Runtime skill registry",
        "",
    ]

    for record in records:
        lines.extend(
            [
                f"- name: {record.name}",
                f"  description: {record.description}",
                f"  source: {record.source}",
                f"  source_path: {record.source_path}",
                f"  anthropic_compatible: {str(record.anthropic_compatible).lower()}",
                f"  pap_contract_path: {record.pap_contract_path or 'null'}",
                f"  anthropic_skill_path: ./anthropic_skills/{record.name.replace('_', '-')}/SKILL.md",
            ]
        )

    lines.extend(
        [
            "",
            "## Detailed protocol specs",
            "",
            "See `.agent/skills/*.md` for local PAP skill contracts. Synced",
            "Anthropic skills are registry entries until they are converted into",
            "local PAP contracts or wired to runtime tool modules.",
            "",
            "## Adding new skills",
            "",
            "1. Create `agent_runtime/tools/<skill_name>.py` for local runtime skills",
            "2. Implement a `run(params: dict) -> dict` function",
            "3. Add the skill name to `tools:` in `.agent/agent.md`",
            "4. Add a matching protocol document under `.agent/skills/`",
            "5. Include `source`, `anthropic_compatible`, `pap_contract_path`, and",
            "   `anthropic_skill_path` metadata in this registry",
            "",
        ]
    )
    return "\n".join(lines)


def sync_to_registry(skills: list[SkillRecord], agent_dir: Path) -> None:
    """Write loaded skills into `.agent/skills.md` with PAP local skills preserved."""
    agent_path = Path(agent_dir)
    if agent_path.name != ".agent" and (agent_path / ".agent").exists():
        agent_path = agent_path / ".agent"
    agent_path.mkdir(parents=True, exist_ok=True)

    merged: dict[str, SkillRecord] = {record.name: record for record in _local_pap_records(agent_path)}
    for skill in skills:
        if skill.name not in merged:
            merged[skill.name] = skill

    (agent_path / "skills.md").write_text(
        _render_registry([merged[name] for name in sorted(merged)]),
        encoding="utf-8",
    )


def write_pap_contracts(skills: list[SkillRecord], source_dir: Path, agent_dir: Path) -> list[Path]:
    """Convert local Anthropic SKILL.md files into `.agent/skills/` contracts."""
    source_root = Path(source_dir)
    agent_path = Path(agent_dir)
    if agent_path.name != ".agent" and (agent_path / ".agent").exists():
        agent_path = agent_path / ".agent"
    skills_path = agent_path / "skills"
    skills_path.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    by_name = {record.name: record for record in skills}
    for skill_md in sorted(source_root.rglob("SKILL.md")):
        record = _record_from_skill_md(skill_md)
        if record.name not in by_name:
            continue
        target = skills_path / f"{record.name}.md"
        target.write_text(anthropic_to_pap(skill_md), encoding="utf-8")
        written.append(target)
    return written
