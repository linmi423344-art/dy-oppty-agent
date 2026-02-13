from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer

from oppty_agent.browser.runner import run_export_flow

DEFAULT_BASE_URL = "https://fxg.jinritemai.com/"
DEFAULT_CONFIG_PATH = "oppty_agent/config/example.yaml"


@dataclass
class AppConfig:
    username: str = ""
    password: str = ""
    headless: bool = False
    data_dir: str = "data"
    base_url: str = DEFAULT_BASE_URL
    ui: dict[str, Any] = field(default_factory=dict)
    download: dict[str, Any] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)


def _coerce_scalar(value: str) -> Any:
    v = value.strip().strip('"').strip("'")
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    if v.isdigit():
        return int(v)
    return v


def _parse_simple_yaml(config_path: str | Path) -> dict[str, Any]:
    root: dict[str, Any] = {}
    current_section: str | None = None
    current_list_key: str | None = None

    for raw_line in Path(config_path).read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()

        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                root[key] = _coerce_scalar(value)
                current_section = None
                current_list_key = None
            else:
                root[key] = {}
                current_section = key
                current_list_key = None
            continue

        if indent >= 2 and current_section is not None:
            if stripped.startswith("- ") and current_list_key is not None:
                root[current_section][current_list_key].append(_coerce_scalar(stripped[2:].strip()))
                continue

            if ":" in stripped:
                key, value = stripped.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value:
                    root[current_section][key] = _coerce_scalar(value)
                    current_list_key = None
                else:
                    root[current_section][key] = []
                    current_list_key = key

    return root


def load_config(config_path: str | Path) -> AppConfig:
    raw = _parse_simple_yaml(config_path)
    return AppConfig(
        username=str(raw.get("username", "")),
        password=str(raw.get("password", "")),
        headless=bool(raw.get("headless", False)),
        data_dir=str(raw.get("data_dir", "data")),
        base_url=str(raw.get("base_url", DEFAULT_BASE_URL)),
        ui=raw.get("ui", {}),
        download=raw.get("download", {}),
        safety=raw.get("safety", {}),
    )


def login(config: AppConfig) -> None:
    """Login flow scaffold with safe persistent context cleanup."""
    from playwright.sync_api import sync_playwright

    context: Any | None = None
    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(Path(config.data_dir) / "browser-profile"),
                headless=config.headless,
            )
            page = context.new_page()
            page.goto(config.base_url)
    finally:
        if context is not None:
            context.close()


def run(config: AppConfig) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    result = run_export_flow(config=config, run_id=run_id)
    return result.manifest_path


app = typer.Typer(help="Opportunity export CLI")


@app.command()
def login_cmd(config: str = typer.Option(DEFAULT_CONFIG_PATH, "--config")) -> None:
    login(load_config(config))


@app.command()
def run_cmd(config: str = typer.Option(DEFAULT_CONFIG_PATH, "--config")) -> None:
    try:
        run(load_config(config))
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


def main(argv: list[str] | None = None) -> int:
    command = typer.main.get_command(app)
    try:
        command.main(args=argv, prog_name="oppty-agent", standalone_mode=False)
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
