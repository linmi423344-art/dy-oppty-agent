from __future__ import annotations

import subprocess
import sys


def test_cli_help_works() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "oppty_agent.cli", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage" in result.stdout


def test_imports_succeed() -> None:
    import oppty_agent  # noqa: F401
    import oppty_agent.browser.runner  # noqa: F401
    import oppty_agent.etl.parse_export  # noqa: F401
    import oppty_agent.selection.scoring  # noqa: F401
