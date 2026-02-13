from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oppty_agent.browser.artifacts import POST_EXPORT_SCREENSHOT, RUN_MANIFEST_NAME, stop_screenshot_path
from oppty_agent.browser.manifest import CategoryResult, add_category_result, build_run_manifest, sha256_file
from oppty_agent.browser.risk import find_risk_keywords
from oppty_agent.browser.selectors import (
    EXPORT_BUTTON_SELECTORS,
    OPPORTUNITY_CENTER_SELECTORS,
    POTENTIAL_PRODUCTS_SELECTORS,
    RANGE_7_DAYS_SELECTORS,
)
from oppty_agent.browser.state_machine import WorkerState


@dataclass
class BrowserRunResult:
    manifest_path: Path
    risk_flags: list[str]


def _latest_file(path: Path) -> Path | None:
    files = [f for f in path.glob("*") if f.is_file()]
    if not files:
        return None
    return sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)[0]


def _collect_risk(page: Any, run_dir: Path, risk_keywords: list[str]) -> list[str]:
    body_text = page.inner_text("body")
    matched = find_risk_keywords(body_text, keywords=risk_keywords)
    if matched:
        reason = "_".join(matched)
        screenshot_path = stop_screenshot_path(run_dir, reason)
        page.screenshot(path=str(screenshot_path), full_page=True)
    return matched


def _safe_click(page: Any, candidates: list[str]) -> None:
    for locator in candidates:
        node = page.locator(locator).first
        if node.count() > 0:
            node.click()
            return
    raise RuntimeError(f"None of locators matched: {candidates}")


def run_export_flow(config: Any, run_id: str) -> BrowserRunResult:
    from playwright.sync_api import sync_playwright

    raw_root = Path(config.data_dir) / "raw" / run_id
    raw_root.mkdir(parents=True, exist_ok=True)
    manifest = build_run_manifest(run_id=run_id, base_url=config.base_url)
    manifest_path = raw_root / RUN_MANIFEST_NAME

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        state = WorkerState.OPEN_BASE_URL
        page.goto(config.base_url)
        risk_flags = _collect_risk(page, raw_root, config.safety["risk_keywords"])
        if risk_flags:
            manifest["risk_flags"] = risk_flags
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
            context.close()
            browser.close()
            raise RuntimeError("Risk detected, worker stopped")

        state = WorkerState.OPEN_OPPORTUNITY_CENTER
        _safe_click(page, OPPORTUNITY_CENTER_SELECTORS)

        state = WorkerState.OPEN_POTENTIAL_EXPLOSIVE_PRODUCTS
        _safe_click(page, POTENTIAL_PRODUCTS_SELECTORS)

        state = WorkerState.SET_RANGE_7_DAYS
        _safe_click(page, RANGE_7_DAYS_SELECTORS)

        state = WorkerState.LOOP_CATEGORIES
        for category in config.ui["categories"]:
            category_dir = raw_root / category
            category_dir.mkdir(parents=True, exist_ok=True)
            screenshots: list[str] = []

            _safe_click(page, [f"text={category}"])
            state = WorkerState.EXPORT
            with page.expect_download(timeout=config.download["timeout_ms"]) as download_info:
                _safe_click(page, EXPORT_BUTTON_SELECTORS)
            download = download_info.value
            temp_target = category_dir / download.suggested_filename
            download.save_as(str(temp_target))

            latest_export = _latest_file(category_dir)
            if latest_export is None:
                add_category_result(
                    manifest,
                    CategoryResult(
                        category=category,
                        status="failed",
                        screenshots=screenshots,
                        message="No exported file found after download",
                    ),
                )
                continue

            final_target = category_dir / latest_export.name
            if final_target != latest_export:
                shutil.move(str(latest_export), str(final_target))

            snap_path = category_dir / POST_EXPORT_SCREENSHOT
            page.screenshot(path=str(snap_path), full_page=True)
            screenshots.append(str(snap_path.relative_to(raw_root)))

            add_category_result(
                manifest,
                CategoryResult(
                    category=category,
                    status="success",
                    download_path=str(final_target.relative_to(raw_root)),
                    sha256=sha256_file(final_target),
                    screenshots=screenshots,
                    message=f"Completed state={state.value}",
                ),
            )
            state = WorkerState.LOOP_CATEGORIES

        state = WorkerState.DONE
        manifest["final_state"] = state.value
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        context.close()
        browser.close()

    return BrowserRunResult(manifest_path=manifest_path, risk_flags=manifest["risk_flags"])
