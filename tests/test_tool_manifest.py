"""Tests for ToolManifest class."""

from __future__ import annotations

from pathlib import Path
import pytest

from agent_runtime.tool_manifest import ToolManifest


def test_list_local(tmp_path: Path) -> None:
    local_dir = tmp_path / "local_skills"
    local_dir.mkdir()

    # Create dummy local skills
    (local_dir / "search_web.md").write_text("---id: search_web---")
    (local_dir / "query_db.md").write_text("---id: query_db---")
    (local_dir / "README.md").write_text("readme info")
    (local_dir / "_template.md").write_text("template info")

    manifest = ToolManifest(local_skills_dir=local_dir)
    local_skills = manifest.list_local()

    assert local_skills == ["query_db", "search_web"]


def test_list_global(tmp_path: Path) -> None:
    global_dir = tmp_path / "global_skills"
    global_dir.mkdir()

    # Create direct file
    (global_dir / "pdf.md").write_text("---id: pdf---")
    (global_dir / "README.md").write_text("readme")

    # Create folder with SKILL.md
    xlsx_dir = global_dir / "xlsx"
    xlsx_dir.mkdir()
    (xlsx_dir / "SKILL.md").write_text("---id: xlsx---")

    # Create folder WITHOUT SKILL.md (should not be treated as a global skill)
    other_dir = global_dir / "other_folder"
    other_dir.mkdir()

    manifest = ToolManifest(global_skills_dir=global_dir)
    global_skills = manifest.list_global()

    assert global_skills == ["pdf", "xlsx"]


def test_list_all(tmp_path: Path) -> None:
    local_dir = tmp_path / "local_skills"
    local_dir.mkdir()
    global_dir = tmp_path / "global_skills"
    global_dir.mkdir()

    (local_dir / "search_web.md").write_text("local")
    (local_dir / "pdf.md").write_text("local pdf")  # Local override

    (global_dir / "pdf.md").write_text("global pdf")
    (global_dir / "xlsx.md").write_text("global xlsx")

    manifest = ToolManifest(local_skills_dir=local_dir, global_skills_dir=global_dir)
    
    assert manifest.list_local() == ["pdf", "search_web"]
    assert manifest.list_global() == ["pdf", "xlsx"]
    assert manifest.list_all() == ["pdf", "search_web", "xlsx"]


def test_is_local_override(tmp_path: Path) -> None:
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    global_dir = tmp_path / "global"
    global_dir.mkdir()

    (local_dir / "pdf.md").write_text("local")
    (local_dir / "search_web.md").write_text("local")
    (global_dir / "pdf.md").write_text("global")

    manifest = ToolManifest(local_skills_dir=local_dir, global_skills_dir=global_dir)
    
    assert manifest.is_local_override("pdf") is True
    assert manifest.is_local_override("search_web") is False
    assert manifest.is_local_override("xlsx") is False


def test_get_skill_contract_path(tmp_path: Path) -> None:
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    global_dir = tmp_path / "global"
    global_dir.mkdir()

    # 1. Local override
    local_search = local_dir / "search_web.md"
    local_search.write_text("local search")
    
    global_search = global_dir / "search_web.md"
    global_search.write_text("global search")

    # 2. Global direct file
    global_pdf = global_dir / "pdf.md"
    global_pdf.write_text("global pdf")

    # 3. Global subdirectory
    xlsx_sub = global_dir / "xlsx"
    xlsx_sub.mkdir()
    global_xlsx = xlsx_sub / "SKILL.md"
    global_xlsx.write_text("global xlsx sub")

    manifest = ToolManifest(local_skills_dir=local_dir, global_skills_dir=global_dir)

    # Search: local should be returned
    assert manifest.get_skill_contract_path("search_web") == local_search
    # PDF: global file should be returned
    assert manifest.get_skill_contract_path("pdf") == global_pdf
    # XLSX: global sub file should be returned
    assert manifest.get_skill_contract_path("xlsx") == global_xlsx
    # Non-existent
    assert manifest.get_skill_contract_path("non_existent") is None


def test_missing_directories() -> None:
    # Directories do not exist, should not crash and return empty lists
    manifest = ToolManifest(
        local_skills_dir="non_existent_local_dir_path",
        global_skills_dir="non_existent_global_dir_path",
    )
    assert manifest.list_local() == []
    assert manifest.list_global() == []
    assert manifest.list_all() == []
    assert manifest.is_local_override("any") is False
    assert manifest.get_skill_contract_path("any") is None
