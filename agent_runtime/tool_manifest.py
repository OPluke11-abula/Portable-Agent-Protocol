"""Tool Manifest managing Local vs Global skill registries for the Portable Agent Protocol."""

from __future__ import annotations

from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


class ToolManifest:
    """Manages local and global skill registries, detecting overrides and global fallbacks."""

    def __init__(
        self,
        local_skills_dir: str | Path | None = None,
        global_skills_dir: str | Path | None = None,
    ) -> None:
        """Initialize the ToolManifest.

        Parameters
        ----------
        local_skills_dir : str | Path | None
            Path to local skills directory. Defaults to '.agent/skills/'.
        global_skills_dir : str | Path | None
            Path to global skills directory. Defaults to '~/.gemini/antigravity/skills/'.
        """
        if local_skills_dir is not None:
            self.local_skills_dir = Path(local_skills_dir)
        else:
            self.local_skills_dir = Path(".agent/skills")

        if global_skills_dir is not None:
            self.global_skills_dir = Path(global_skills_dir)
        else:
            self.global_skills_dir = Path("~/.gemini/antigravity/skills").expanduser()

        logger.debug(
            "Initialized ToolManifest with local=%s, global=%s",
            self.local_skills_dir,
            self.global_skills_dir,
        )

    def list_local(self) -> list[str]:
        """List all project-local skill IDs.

        Returns
        -------
        list[str]
            Sorted list of local skill contract stems.
        """
        if not self.local_skills_dir.exists() or not self.local_skills_dir.is_dir():
            return []

        skills = []
        for path in self.local_skills_dir.glob("*.md"):
            if path.name.startswith("_") or path.name in ("README.md", "__init__.md"):
                continue
            skills.append(path.stem)
        return sorted(skills)

    def list_global(self) -> list[str]:
        """List all global fallback skill IDs.

        Returns
        -------
        list[str]
            Sorted list of global skill stems.
        """
        if not self.global_skills_dir.exists() or not self.global_skills_dir.is_dir():
            return []

        skills = set()
        # Look for subdirectories containing SKILL.md or just files ending in .md
        for path in self.global_skills_dir.iterdir():
            if path.is_dir():
                if (path / "SKILL.md").exists() or (path / "SKILL.md").is_file():
                    skills.add(path.name)
            elif path.is_file() and path.suffix == ".md":
                if not (path.name.startswith("_") or path.name in ("README.md", "__init__.md")):
                    skills.add(path.stem)
        return sorted(list(skills))

    def list_all(self) -> list[str]:
        """Union of all local and global skill IDs.

        Returns
        -------
        list[str]
            Sorted list of all skill IDs.
        """
        local = self.list_local()
        global_skills = self.list_global()
        return sorted(list(set(local) | set(global_skills)))

    def is_local_override(self, skill_id: str) -> bool:
        """Check if a project-local skill overrides a global skill of the same name.

        Parameters
        ----------
        skill_id : str
            The skill ID to check.

        Returns
        -------
        bool
            True if overridden locally.
        """
        local = self.list_local()
        global_skills = self.list_global()
        return (skill_id in local) and (skill_id in global_skills)

    def get_skill_contract_path(self, skill_id: str) -> Path | None:
        """Find the contract path for a given skill ID, enforcing local override > global fallback.

        Parameters
        ----------
        skill_id : str
            The skill ID to resolve.

        Returns
        -------
        Path | None
            The Path to the skill contract, or None if not found in either layer.
        """
        # 1. Check local override
        local_path = self.local_skills_dir / f"{skill_id}.md"
        if local_path.exists() and local_path.is_file():
            return local_path

        # 2. Check global fallback
        if self.global_skills_dir.exists() and self.global_skills_dir.is_dir():
            # A. Under skill_id/SKILL.md
            global_sub_path = self.global_skills_dir / skill_id / "SKILL.md"
            if global_sub_path.exists() and global_sub_path.is_file():
                return global_sub_path

            # B. Under skill_id.md
            global_file_path = self.global_skills_dir / f"{skill_id}.md"
            if global_file_path.exists() and global_file_path.is_file():
                return global_file_path

        return None
