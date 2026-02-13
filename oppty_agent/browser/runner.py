from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from oppty_agent.browser.manifest import add_category_result, build_manifest, compute_sha256, write_manifest
from oppty_agent.browser.state_machine import (
    check_page_risk,
    navigate_export_page,
    save_named_screenshot,
    select_category,
)

CATEGORIES = ["洗护清洁剂", "卫生巾", "纸", "香薰"]


@dataclass
class BrowserRunResult:
    exit_code: int
    manifest_path: Path


def _risk_reason_from_keywords(keywords: list[str]) -> str:
    if not keywords:
        return "risk_detected"
    return "_".join(dict.fromkeys(keywords))


def run_export_first(
    *,
    base_url: str,
    data_dir: str,
    profile_dir: str,
    headless: bool,
    download_timeout_s: int,
) -> BrowserRunResult:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    run_dir = Path(data_dir) / "runs" / run_id
    raw_dir = Path(data_dir) / "raw" / run_id
    screenshots_dir = run_dir / "screenshots"
    manifest_path = run_dir / "run_manifest.json"

    manifest = build_manifest(run_id, base_url)

    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        manifest["risk_flags"] = ["playwright_not_installed"]
        write_manifest(manifest, manifest_path)
        return BrowserRunResult(exit_code=3, manifest_path=manifest_path)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=headless,
            accept_downloads=True,
        )
        try:
            page = context.new_page()
            page.goto(base_url)
            save_named_screenshot(page, screenshots_dir, "STEP_base_url_loaded.png")

            risk = check_page_risk(page)
            if risk.blocked:
                reason = _risk_reason_from_keywords(risk.matched_keywords)
                save_named_screenshot(page, screenshots_dir, f"STOP_{reason}.png")
                manifest["risk_flags"] = risk.matched_keywords
                write_manifest(manifest, manifest_path)
                return BrowserRunResult(exit_code=3, manifest_path=manifest_path)

            navigate_export_page(page, screenshots_dir)

            risk = check_page_risk(page)
            if risk.blocked:
                reason = _risk_reason_from_keywords(risk.matched_keywords)
                save_named_screenshot(page, screenshots_dir, f"STOP_{reason}.png")
                manifest["risk_flags"] = risk.matched_keywords
                write_manifest(manifest, manifest_path)
                return BrowserRunResult(exit_code=3, manifest_path=manifest_path)

            for category in CATEGORIES:
                try:
                    select_category(page, category)
                    category_dir = raw_dir / category
                    category_dir.mkdir(parents=True, exist_ok=True)
                    with page.expect_download(timeout=download_timeout_s * 1000) as download_info:
                        page.get_by_text("导出", exact=False).click()
                    download = download_info.value
                    filename = download.suggested_filename or f"{category}.csv"
                    saved_path = category_dir / filename
                    download.save_as(str(saved_path))

                    add_category_result(
                        manifest,
                        category=category,
                        status="downloaded",
                        downloaded_file=str(saved_path),
                        sha256=compute_sha256(saved_path),
                    )
                    save_named_screenshot(page, screenshots_dir, f"OK_export_{category}.png")
                except Exception as exc:  # noqa: BLE001
                    add_category_result(
                        manifest,
                        category=category,
                        status="failed",
                        error=str(exc),
                    )
                    save_named_screenshot(page, screenshots_dir, f"FAIL_export_{category}.png")
        finally:
            context.close()

    write_manifest(manifest, manifest_path)
    return BrowserRunResult(exit_code=0, manifest_path=manifest_path)
