from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oppty_agent.browser.runner import run_export_first

DEFAULT_BASE_URL = "https://fxg.jinritemai.com/"


@dataclass
class AppConfig:
    username: str = ""
    password: str = ""
    headless: bool = False
    data_dir: str = "data"
    base_url: str = DEFAULT_BASE_URL
    ui_timeout_s: int = 20
    download_timeout_s: int = 60


def _parse_simple_yaml(config_path: str | Path) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for raw_line in Path(config_path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value.lower() == "true":
            parsed[key] = True
        elif value.lower() == "false":
            parsed[key] = False
        else:
            parsed[key] = value
    return parsed


def load_config(config_path: str | Path) -> AppConfig:
    raw = _parse_simple_yaml(config_path)
    return AppConfig(
        username=str(raw.get("username", "")),
        password=str(raw.get("password", "")),
        headless=bool(raw.get("headless", False)),
        data_dir=str(raw.get("data_dir", "data")),
        base_url=str(raw.get("base_url", DEFAULT_BASE_URL)),
        ui_timeout_s=int(raw.get("ui_timeout_s", 20)),
        download_timeout_s=int(raw.get("download_timeout_s", 60)),
    )


def login(config: AppConfig, profile_dir: str) -> None:
    """Login flow scaffold with safe persistent context cleanup."""
    context: Any | None = None
    try:
        try:
            from playwright.sync_api import sync_playwright
        except ModuleNotFoundError:
            return

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=config.headless,
            )
            page = context.new_page()
            page.goto(config.base_url)
    finally:
        if context is not None:
            context.close()


def run(config: AppConfig, profile_dir: str = "data/profile") -> Path:
    result = run_export_first(
        base_url=config.base_url,
        data_dir=config.data_dir,
        profile_dir=profile_dir,
        headless=config.headless,
        download_timeout_s=config.download_timeout_s,
    )
    return result.manifest_path


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oppty-agent")
    parser.add_argument("--config", default=None)
    parser.add_argument("--profile-dir", default="data/profile")

    subparsers = parser.add_subparsers(dest="command", required=True)
    login_parser = subparsers.add_parser("login")
    login_parser.add_argument("--config", default=None)
    login_parser.add_argument("--profile-dir", default="data/profile")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", default=None)
    run_parser.add_argument("--profile-dir", default="data/profile")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _get_parser()
    args = parser.parse_args(argv)
    config_path = args.config or "oppty_agent/config/example.yaml"
    config = load_config(config_path)

    if args.command == "login":
        login(config, profile_dir=args.profile_dir)
    elif args.command == "run":
        result = run_export_first(
            base_url=config.base_url,
            data_dir=config.data_dir,
            profile_dir=args.profile_dir,
            headless=config.headless,
            download_timeout_s=config.download_timeout_s,
        )
        return result.exit_code
    else:
        parser.error(f"Unknown command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
