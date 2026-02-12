"""Playwright browser runner skeleton."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

DOUYIN_SHOP_BASE_URL = "https://fxg.jinritemai.com/"


def open_persistent_login(profile_dir: Path, base_url: str = DOUYIN_SHOP_BASE_URL) -> None:
    """Open persistent Chromium profile and wait for manual close."""
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
        )
        page = context.new_page()
        page.goto(base_url, wait_until="domcontentloaded")
        page.wait_for_timeout(60_000 * 60)
