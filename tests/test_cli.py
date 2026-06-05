"""Tests for the reference CLI entrypoint in cli.py."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from cli import main


class TestCLI:
    def test_cli_validate(self) -> None:
        # Validate using default .agent/agent.md
        exit_code = main(["validate"])
        assert exit_code == 0

    def test_cli_validate_option(self) -> None:
        # Validate using --validate option
        exit_code = main(["--validate"])
        assert exit_code == 0

    def test_cli_list_skills(self) -> None:
        exit_code = main(["--list-skills"])
        assert exit_code == 0

    def test_cli_describe_skill(self, capsys) -> None:
        exit_code = main(["--describe-skill", "search_web"])
        assert exit_code == 0
        captured = capsys.readouterr()
        
        stdout = captured.out
        start_idx = stdout.find("{")
        assert start_idx != -1
        contract = json.loads(stdout[start_idx:])
        assert contract["id"] == "search_web"

    def test_cli_describe_nonexistent_skill(self) -> None:
        exit_code = main(["--describe-skill", "nonexistent_skill"])
        assert exit_code == 1

    def test_cli_memory_write_and_read(self, capsys) -> None:
        # Write to memory
        exit_code_write = main(["--memory-write", "cli_test_key", "cli_val"])
        assert exit_code_write == 0

        # Read back from memory
        exit_code_read = main(["--memory-read", "cli_test_key"])
        assert exit_code_read == 0
        captured = capsys.readouterr()
        
        stdout = captured.out
        # Find the line containing the output value (starts with " or is a JSON string)
        # We can find the first quote character or load the last line
        start_idx = stdout.rfind('"')
        assert start_idx != -1
        # The value might be enclosed in double quotes as a JSON string, e.g. "cli_val"
        first_quote = stdout.find('"', stdout.find("AgentEngine initialised"))
        if first_quote != -1:
            val_str = stdout[first_quote:].strip()
            value = json.loads(val_str)
        else:
            lines = [line.strip() for line in stdout.splitlines() if line.strip()]
            value = json.loads(lines[-1])
        assert value == "cli_val"

    def test_cli_workflow_run_and_resume(self, tmp_path, capsys, monkeypatch) -> None:
        config_path = _write_workspace_cli(
            tmp_path,
            """\
            ---
            name: sample
            steps:
              - id: step_one
                tool: fake_tool
                params:
                  val: "test"
              - id: step_two
                action: respond
                depends_on: [step_one]
                params:
                  msg: "{{ step_one.output.processed }}"
            ---
            # Sample Workflow
            """,
        )

        from agent_runtime.engine import AgentEngine
        original_run = AgentEngine.run

        def mock_run(self_engine, tool, params=None):
            if tool == "fake_tool":
                return {"processed": f"PROCESSED_{params['val']}"}
            return original_run(self_engine, tool, params)

        monkeypatch.setattr(AgentEngine, "run", mock_run)

        # Run workflow via CLI
        exit_code = main(["--config", str(config_path), "--run-workflow", "sample"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "PROCESSED_test" in captured.out

    def test_cli_workflow_run_and_resume_failure(self, tmp_path, capsys, monkeypatch) -> None:
        config_path = _write_workspace_cli(
            tmp_path,
            """\
            ---
            name: sample
            steps:
              - id: step_one
                tool: fake_tool
                params:
                  val: "test"
              - id: step_two
                tool: fake_tool
                depends_on: [step_one]
                params:
                  val: "fail"
            ---
            # Sample Workflow
            """,
        )

        from agent_runtime.engine import AgentEngine

        should_fail = True
        def mock_run(self_engine, tool, params=None):
            if tool == "fake_tool":
                val = params.get("val")
                if val == "fail" and should_fail:
                    raise ValueError("CLI failure test")
                return {"processed": val}
            raise ValueError(f"Unknown tool: {tool}")

        monkeypatch.setattr(AgentEngine, "run", mock_run)

        # Run first time - should fail
        exit_code = main(["--config", str(config_path), "--run-workflow", "sample"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Workflow execution failed" in captured.err

        # Get session id
        engine = AgentEngine(config_path)
        session_keys = [k for k in engine.memory.list_keys() if k.startswith("workflow:sample:session:")]
        assert len(session_keys) == 1
        session_id = session_keys[0].split(":")[-1]

        # Resume execution - make the tool succeed now
        should_fail = False
        exit_code_resume = main([
            "--config", str(config_path),
            "--run-workflow", "sample",
            "--resume-session", session_id
        ])
        assert exit_code_resume == 0
        captured_resume = capsys.readouterr()
        assert "Resuming workflow" in captured_resume.out


    def test_cli_handoff(self, tmp_path, capsys) -> None:
        import shutil
        # Setup source agent
        config_path_src = _write_workspace_cli(tmp_path / "src", "# Src Agent")
        
        # Setup target agent
        config_path_dest = _write_workspace_cli(tmp_path / "dest", "# Dest Agent")
        
        # Write to source memory
        assert main(["--config", str(config_path_src), "--memory-write", "secret_key", "secret_val"]) == 0
        
        # Export handoff from source via CLI
        export_payload = json.dumps({
            "task_state": "Completed task A.",
            "pending_steps": ["Do task B."],
            "context_summary": "Planner done.",
            "memory_keys": ["secret_key"],
            "handoff_id": "cli-handoff-id"
        })
        
        exit_code_export = main(["--config", str(config_path_src), "--export-handoff", export_payload])
        assert exit_code_export == 0
        
        # Verify source file was written
        src_file = tmp_path / "src" / ".agent" / "memory" / "handoff" / "cli-handoff-id.json"
        assert src_file.exists()
        
        # Move/copy file to dest handoff dir
        dest_file = tmp_path / "dest" / ".agent" / "memory" / "handoff" / "cli-handoff-id.json"
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        
        # Import handoff in dest via CLI
        exit_code_import = main(["--config", str(config_path_dest), "--import-handoff", "cli-handoff-id"])
        assert exit_code_import == 0
        
        # Verify dest memory has key populated
        capsys.readouterr()  # clear buffer
        exit_code_read = main(["--config", str(config_path_dest), "--memory-read", "secret_key"])
        assert exit_code_read == 0
        captured = capsys.readouterr()
        assert "secret_val" in captured.out


def _write_workspace_cli(tmp_path: Path, workflow_body: str) -> Path:

    import textwrap
    agent_dir = tmp_path / ".agent"
    workflows_dir = agent_dir / "workflows"
    skills_dir = agent_dir / "skills"
    workflows_dir.mkdir(parents=True)
    skills_dir.mkdir()
    (skills_dir / "fake_tool.md").write_text("# fake_tool\n", encoding="utf-8")
    (workflows_dir / "sample.md").write_text(textwrap.dedent(workflow_body), encoding="utf-8")

    memory_dir = agent_dir / "memory"
    memory_dir.mkdir()

    config = textwrap.dedent(
        f"""\
        ---
        protocol_version: "1.0.0"
        min_runtime_version: "0.1.0"
        name: test-agent
        version: "0.1.0"
        purpose: Test CLI.
        language: en-US
        authorization_level: interactive-approval
        use_case_tags: [test]
        tools:
          - fake_tool
        protocol:
          root: .agent/
          manifest: .agent/agent.md
          directories:
            skills: .agent/skills/
            workflows: .agent/workflows/
        memory:
          backend: local
          path: {memory_dir.as_posix()}
        ---
        # Test Agent
        """
    )
    path = agent_dir / "agent.md"
    path.write_text(config, encoding="utf-8")
    return path

