from oppty_agent.cli import main


def test_cli_help_smoke() -> None:
    assert main(["--help"]) == 0
