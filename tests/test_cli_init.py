"""Tests for the reference CLI 'init' subcommand in cli.py."""

from __future__ import annotations

from pathlib import Path
import pytest

from cli import main


def test_cli_init_dry_run(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    
    exit_code = main([
        "init", 
        "--project-name", "dry-proj", 
        "--agent-name", "dry-agent", 
        "--skills", "search_web,query_db", 
        "--dry-run"
    ])
    assert exit_code == 0
    
    # Verify no directories or files actually created
    assert not (tmp_path / ".agent").exists()
    
    captured = capsys.readouterr()
    assert "[Dry Run] Would create directory:" in captured.out
    assert "[Dry Run] Would create file:" in captured.out
    assert "agent.md" in captured.out
    assert "skills.md" in captured.out
    assert "prompts.md" in captured.out
    assert "memory.md" in captured.out
    assert "workflows.md" in captured.out
    assert "search_web.md" in captured.out
    assert "query_db.md" in captured.out


def test_cli_init_real_creation(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    
    exit_code = main([
        "init", 
        "--project-name", "test-proj", 
        "--agent-name", "test-agent", 
        "--skills", "tool1,tool2"
    ])
    assert exit_code == 0
    
    agent_dir = tmp_path / ".agent"
    assert agent_dir.exists()
    assert (agent_dir / "skills").is_dir()
    assert (agent_dir / "prompts").is_dir()
    assert (agent_dir / "workflows").is_dir()
    assert (agent_dir / "memory").is_dir()
    assert (agent_dir / "knowledge_base").is_dir()
    
    assert (agent_dir / "agent.md").is_file()
    assert (agent_dir / "skills.md").is_file()
    assert (agent_dir / "prompts.md").is_file()
    assert (agent_dir / "memory.md").is_file()
    assert (agent_dir / "workflows.md").is_file()
    
    assert (agent_dir / "skills" / "tool1.md").is_file()
    assert (agent_dir / "skills" / "tool2.md").is_file()

    # Read and verify content of agent.md
    agent_content = (agent_dir / "agent.md").read_text(encoding="utf-8")
    assert 'name: "test-agent"' in agent_content
    assert '- tool1' in agent_content
    assert '- tool2' in agent_content
    
    # Verify skill file schema correctness by running validation
    # Since agent-schema.json won't be found in the temp directory's parent,
    # we copy the schemas into a "spec" folder in the temp path or mock validation.
    # Actually, let's copy the schema files to spec/ relative to the temp directory!
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir(exist_ok=True)
    
    # Read schemas from original project root and write to temp spec/
    original_root = Path(__file__).parent.parent
    for schema_file in original_root.glob("spec/*.json"):
        content = schema_file.read_text(encoding="utf-8")
        (spec_dir / schema_file.name).write_text(content, encoding="utf-8")
        
    exit_code_validate = main([
        "--config", str(agent_dir / "agent.md"),
        "validate"
    ])
    assert exit_code_validate == 0
