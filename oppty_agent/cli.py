from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from oppty_agent.browser.manifest import build_run_manifest

DEFAULT_BASE_URL = "https://fxg.jinritemai.com/"


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


def _default_runner(config: AppConfig, run_id: str) -> Any:
    from oppty_agent.browser.runner import run_export_flow

    return run_export_flow(config=config, run_id=run_id)


def _write_dry_run_manifest(config: AppConfig, run_id: str) -> Path:
    raw_root = Path(config.data_dir) / "raw" / run_id
    raw_root.mkdir(parents=True, exist_ok=True)
    manifest = build_run_manifest(run_id=run_id, base_url=config.base_url)
    manifest["mode"] = "dry-run"
    manifest["config"] = {
        "headless": config.headless,
        "data_dir": config.data_dir,
        "base_url": config.base_url,
        "ui": config.ui,
        "download": config.download,
        "safety": config.safety,
    }
    manifest_path = raw_root / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path


def run(config: AppConfig, dry_run: bool = False, runner: Callable[[AppConfig, str], Any] | None = None) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    if dry_run:
        return _write_dry_run_manifest(config=config, run_id=run_id)

    effective_runner = runner or _default_runner
    result = effective_runner(config, run_id)
    return result.manifest_path


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oppty-agent")
    parser.add_argument("--config", default=None)

    subparsers = parser.add_subparsers(dest="command", required=True)
    login_parser = subparsers.add_parser("login")
    login_parser.add_argument("--config", default=None)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", default=None)
    run_parser.add_argument("--dry-run", action="store_true", default=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _get_parser()
    args = parser.parse_args(argv)
    config_path = args.config or "oppty_agent/config/example.yaml"
    config = load_config(config_path)

    if args.command == "login":
        login(config)
    elif args.command == "run":
        try:
            run(config, dry_run=args.dry_run)
        except RuntimeError:
            return 1
    else:
        parser.error(f"Unknown command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
