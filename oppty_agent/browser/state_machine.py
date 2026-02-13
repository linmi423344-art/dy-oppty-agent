from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from oppty_agent.browser.risk import detect_risk

logger = logging.getLogger(__name__)


class BrowserStateMachine:
    def __init__(self, page: object, run_id: str, screenshots_dir: Path, safety_max_clicks: int, selectors: dict[str, str], nav_candidates: dict[str, list[str]], ui_module_label: str, window_label: str) -> None:
        self.page = page
        self.run_id = run_id
        self.screenshots_dir = screenshots_dir
        self.safety_max_clicks = safety_max_clicks
        self.selectors = selectors
        self.nav_candidates = nav_candidates
        self.ui_module_label = ui_module_label
        self.window_label = window_label
        self.click_count = 0

    def _take_screenshot(self, name: str) -> str:
        path = self.screenshots_dir / f"{name}.png"
        self.page.screenshot(path=str(path), full_page=True)
        return str(path)

    def _bounded_click(self, locator: object) -> None:
        self.click_count += 1
        if self.click_count > self.safety_max_clicks:
            raise RuntimeError(f"Exceeded safety.max_clicks: {self.safety_max_clicks}")
        locator.click(timeout=5000)

    def _run_step(self, name: str, fn: Callable[[], None]) -> str | None:
        logger.info("Step start: %s", name)
        risk_reason = detect_risk(self.page)
        if risk_reason:
            self._take_screenshot(f"STOP_{risk_reason}")
            return risk_reason
        try:
            fn()
            self._take_screenshot(name)
            logger.info("Step ok: %s", name)
            return None
        except Exception:
            self._take_screenshot(f"FAIL_{name}")
            raise

    def go_to_base(self, base_url: str) -> str | None:
        return self._run_step("go_to_base", lambda: self.page.goto(base_url, wait_until="domcontentloaded", timeout=30000))

    def navigate_to_opportunity_center(self) -> str | None:
        def _do() -> None:
            for candidate in self.nav_candidates["product"]:
                loc = self.page.get_by_text(candidate, exact=False)
                if loc.count() > 0:
                    self._bounded_click(loc.first)
                    break
            for candidate in self.nav_candidates["opportunity_center"]:
                loc = self.page.get_by_text(candidate, exact=False)
                if loc.count() > 0:
                    self._bounded_click(loc.first)
                    return
            raise RuntimeError("Cannot find 商机中心 nav")

        return self._run_step("navigate_to_opportunity_center", _do)

    def select_module_potential_bestseller(self) -> str | None:
        return self._run_step(
            "select_module_potential_bestseller",
            lambda: self._bounded_click(self.page.get_by_text(self.ui_module_label, exact=False).first),
        )

    def set_window_7d(self) -> str | None:
        return self._run_step(
            "set_window_7d",
            lambda: self._bounded_click(self.page.get_by_text(self.window_label, exact=False).first),
        )

    def set_category(self, category_name: str) -> str | None:
        def _do() -> None:
            selector = self.selectors.get("category_dropdown")
            if selector:
                self._bounded_click(self.page.locator(selector).first)
            else:
                self._bounded_click(self.page.get_by_role("combobox").first)
            self._bounded_click(self.page.get_by_text(category_name, exact=False).first)

        return self._run_step(f"set_category_{category_name}", _do)

    def export_and_download(self, export_candidates: list[str], category_name: str) -> str | None:
        def _do() -> None:
            for text in export_candidates:
                loc = self.page.get_by_text(text, exact=False)
                if loc.count() > 0:
                    self._bounded_click(loc.first)
                    return
            raise RuntimeError("Cannot find export button")

        return self._run_step(f"export_{category_name}", _do)
