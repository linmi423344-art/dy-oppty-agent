"""CLI entrypoints for dy-oppty-agent."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
import yaml

from oppty_agent.browser.runner import open_persistent_login

app = typer.Typer(help="Douyin Shop Opportunity Center Agent CLI")
LOGGER = logging.getLogger("oppty_agent")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def load_yaml_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise typer.BadParameter(f"Config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise typer.BadParameter("Config file must contain a YAML object at top level")
    return data


def create_run_id() -> str:
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]
    return f"run_{ts}_{suffix}"


@app.command()
def login(
    profile_dir: Annotated[Path, typer.Option("--profile-dir")] = Path("data/profile"),
) -> None:
    """Open persistent browser context for manual login."""
    configure_logging()
    profile_dir.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Launching login session with profile dir: %s", profile_dir)
    open_persistent_login(profile_dir=profile_dir)


@app.command()
def run(
    config: Annotated[Path, typer.Option("--config")] = Path("oppty_agent/config/example.yaml"),
) -> None:
    """Initialize a run folder and placeholder run manifest."""
    configure_logging()
    config_data = load_yaml_config(config)
    run_id = create_run_id()

    run_dir = Path("data") / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "status": "initialized",
        "config_path": str(config),
        "config": config_data,
        "notes": "Scaffold placeholder manifest",
    }

    manifest_path = run_dir / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    LOGGER.info("Run initialized: %s", run_id)
    LOGGER.info("Manifest written to: %s", manifest_path)
    typer.echo(run_id)


@app.command()
def etl(run_id: Annotated[str, typer.Option("--run-id")]) -> None:
    """Placeholder ETL command."""
    configure_logging()
    LOGGER.info("ETL placeholder invoked for run_id=%s", run_id)


@app.command()
def select(
    run_id: Annotated[str, typer.Option("--run-id")],
    config: Annotated[Path, typer.Option("--config")] = Path("oppty_agent/config/example.yaml"),
) -> None:
    """Placeholder selection command."""
    configure_logging()
    _ = load_yaml_config(config)
    LOGGER.info("Selection placeholder invoked for run_id=%s", run_id)


if __name__ == "__main__":
    app()
