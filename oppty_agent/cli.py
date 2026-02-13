from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oppty_agent.browser.runner import run_export_flow

DEFAULT_BASE_URL = "https://fxg.jinritemai.com/"


@dataclass
class AppConfig:
    username: str = ""
    password: str = ""
    headless: bool = False
    data_dir: str = "data"
    base_url: str = DEFAULT_BASE_URL
    categories: list[str] = field(default_factory=list)
    profile_dir: str = "data/browser-profile"
    ui_module_label: str = "潜力爆品"
    ui_window_label: str = "7天"
    ui_export_button_text_candidates: list[str] = field(default_factory=lambda: ["导出", "导出数据"])
    ui_opportunity_center_nav_candidates: list[str] = field(default_factory=lambda: ["商机中心"])
    ui_product_nav_candidates: list[str] = field(default_factory=lambda: ["商品"])
    download_dir: str = "data/downloads"
    keep_original_filename: bool = True
    selectors: dict[str, str] = field(default_factory=dict)
    safety_max_clicks: int = 50


def _parse_simple_yaml(config_path: str | Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        return loaded or {}
    except ModuleNotFoundError:
        parsed: dict[str, Any] = {}
        for raw_line in Path(config_path).read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            parsed[key.strip()] = value.strip().strip('"').strip("'")
        return parsed


def load_config(config_path: str | Path) -> AppConfig:
    raw = _parse_simple_yaml(config_path)
    ui = raw.get("ui", {})
    download = raw.get("download", {})
    safety = raw.get("safety", {})
    return AppConfig(
        username=str(raw.get("username", "")),
        password=str(raw.get("password", "")),
        headless=bool(raw.get("headless", False)),
        data_dir=str(raw.get("data_dir", "data")),
        base_url=str(raw.get("base_url", DEFAULT_BASE_URL)),
        categories=list(raw.get("categories", [])),
        profile_dir=str(raw.get("profile_dir", Path(raw.get("data_dir", "data")) / "browser-profile")),
        ui_module_label=str(ui.get("module_label", "潜力爆品")),
        ui_window_label=str(ui.get("window_label", "7天")),
        ui_export_button_text_candidates=list(ui.get("export_button_text_candidates", ["导出", "导出数据"])),
        ui_opportunity_center_nav_candidates=list(ui.get("opportunity_center_nav_candidates", ["商机中心"])),
        ui_product_nav_candidates=list(ui.get("product_nav_candidates", ["商品"])),
        download_dir=str(download.get("dir", "data/downloads")),
        keep_original_filename=bool(download.get("keep_original_filename", True)),
        selectors=dict(raw.get("selectors", {})),
        safety_max_clicks=int(safety.get("max_clicks", 50)),
    )


def login(config: AppConfig) -> None:
    context: Any | None = None
    try:
        try:
            from playwright.sync_api import sync_playwright
        except ModuleNotFoundError:
            return

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(Path(config.profile_dir)),
                headless=config.headless,
            )
            page = context.new_page()
            page.goto(config.base_url)
    finally:
        if context is not None:
            context.close()


def run(config: AppConfig) -> tuple[Path, int]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    run_dir = Path(config.data_dir) / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "run_manifest.json"

    manifest = run_export_flow(config, run_id)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    statuses = [entry["status"] for entry in manifest["per_category"]]
    if manifest["risk_flags"] or "RISK_STOP" in statuses:
        return manifest_path, 3
    if statuses and all(status == "SUCCESS" for status in statuses):
        return manifest_path, 0
    return manifest_path, 2


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oppty-agent")
    parser.add_argument("--config", default=None)

    subparsers = parser.add_subparsers(dest="command", required=True)
    login_parser = subparsers.add_parser("login")
    login_parser.add_argument("--config", default=None)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _get_parser()
    args = parser.parse_args(argv)
    config_path = args.config or "oppty_agent/config/example.yaml"
    config = load_config(config_path)

    if args.command == "login":
        login(config)
        return 0
    if args.command == "run":
        _, code = run(config)
        return code
    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
