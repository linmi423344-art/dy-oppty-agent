from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oppty_agent.browser.manifest import build_category_entry, build_run_manifest, utc_now_iso
from oppty_agent.browser.risk import detect_risk
from oppty_agent.browser.state_machine import BrowserStateMachine

logger = logging.getLogger(__name__)


def open_persistent_context(profile_dir: Path, download_dir: Path, headless: bool) -> Any:
    from playwright.sync_api import sync_playwright

    playwright = sync_playwright().start()
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=headless,
        accept_downloads=True,
        downloads_path=str(download_dir),
    )
    context._playwright = playwright
    return context


def ensure_logged_in(page: object) -> None:
    url = page.url
    if "login" in url:
        print("Please login manually in the opened browser. Waiting for console home...")
        page.wait_for_url("**fxg.jinritemai.com/**", timeout=180000)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_export_flow(config: Any, run_id: str) -> dict[str, Any]:
    run_dir = Path(config.data_dir) / "runs" / run_id
    screenshots_dir = run_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    download_tmp_dir = Path(config.download_dir)
    download_tmp_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_run_manifest(
        run_id=run_id,
        base_url=config.base_url,
        module_label=config.ui_module_label,
        window_label=config.ui_window_label,
        categories=config.categories,
    )

    context = open_persistent_context(Path(config.profile_dir), download_tmp_dir, config.headless)
    try:
        page = context.pages[0] if context.pages else context.new_page()
        sm = BrowserStateMachine(
            page=page,
            run_id=run_id,
            screenshots_dir=screenshots_dir,
            safety_max_clicks=config.safety_max_clicks,
            selectors=config.selectors,
            nav_candidates={
                "product": config.ui_product_nav_candidates,
                "opportunity_center": config.ui_opportunity_center_nav_candidates,
            },
            ui_module_label=config.ui_module_label,
            window_label=config.ui_window_label,
        )

        risk = sm.go_to_base(config.base_url)
        ensure_logged_in(page)
        for step in (sm.navigate_to_opportunity_center, sm.select_module_potential_bestseller, sm.set_window_7d):
            risk = risk or step()
            if risk:
                manifest["risk_flags"].append(risk)
                manifest["finished_at"] = utc_now_iso()
                return manifest

        for category in config.categories:
            entry = build_category_entry(category)
            manifest["per_category"].append(entry)
            try:
                risk = detect_risk(page)
                if risk:
                    entry["status"] = "RISK_STOP"
                    entry["error"] = risk
                    stop_path = screenshots_dir / f"STOP_{risk}.png"
                    page.screenshot(path=str(stop_path), full_page=True)
                    entry["screenshots"].append(str(stop_path))
                    manifest["risk_flags"].append(risk)
                    break

                risk = sm.set_category(category)
                if risk:
                    entry["status"] = "RISK_STOP"
                    entry["error"] = risk
                    manifest["risk_flags"].append(risk)
                    break

                before = screenshots_dir / f"before_export_{category}.png"
                page.screenshot(path=str(before), full_page=True)
                entry["screenshots"].append(str(before))

                with page.expect_download(timeout=30000) as dl_info:
                    risk = sm.export_and_download(config.ui_export_button_text_candidates, category)
                if risk:
                    entry["status"] = "RISK_STOP"
                    entry["error"] = risk
                    manifest["risk_flags"].append(risk)
                    break
                download = dl_info.value
                suggested = download.suggested_filename
                extension = Path(suggested).suffix or ".xlsx"
                filename = suggested if config.keep_original_filename else f"{category}{extension}"
                target_dir = Path(config.data_dir) / "raw" / run_id / category
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / f"{_now_stamp()}_{filename}"
                download.save_as(str(target))

                after = screenshots_dir / f"after_download_{category}.png"
                page.screenshot(path=str(after), full_page=True)
                entry["screenshots"].append(str(after))
                entry["status"] = "SUCCESS"
                entry["download_path"] = str(target)
                entry["sha256"] = _sha256(target)
            except Exception as exc:
                logger.exception("Export failed for %s", category)
                fail_shot = screenshots_dir / f"FAIL_{category}.png"
                page.screenshot(path=str(fail_shot), full_page=True)
                entry["screenshots"].append(str(fail_shot))
                entry["status"] = "EXPORT_FAILED"
                entry["error"] = str(exc)

        manifest["finished_at"] = utc_now_iso()
        return manifest
    finally:
        context.close()
        context._playwright.stop()
