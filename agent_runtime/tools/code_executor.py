"""code_executor — stub tool for sandboxed Python execution.

In production, replace the ``subprocess``-based executor with a proper
sandbox (e.g. Docker, gVisor, Pyodide) to prevent untrusted code from
accessing the host system.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def run(params: dict[str, Any]) -> dict[str, Any]:
    """Execute a Python snippet and return stdout/stderr/exit_code.

    Parameters
    ----------
    params:
        code    : str — Python source to execute (required)
        timeout : int — seconds before the process is killed (default 10)

    Returns
    -------
    dict with keys ``stdout``, ``stderr``, and ``exit_code``.
    """
    code: str = params.get("code", "")
    timeout: int = int(params.get("timeout", 10))

    if not code:
        return {"error": "Missing required parameter: code", "stdout": "", "stderr": "", "exit_code": 1}

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
        tmp.write(code)
        tmp_path = Path(tmp.name)

    try:
        proc = subprocess.run(
            [sys.executable, str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds.",
            "exit_code": 124,
        }
    finally:
        tmp_path.unlink(missing_ok=True)
