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
