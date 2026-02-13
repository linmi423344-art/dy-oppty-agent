from __future__ import annotations

from pathlib import Path

from oppty_agent.browser.risk import RiskCheckResult, detect_risk_text


NAV_TIMEOUT_MS = 20_000


def save_named_screenshot(page: object, screenshots_dir: Path, name: str) -> Path:
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    output_path = screenshots_dir / name
    # Playwright page typed as object to keep pure unit tests free of playwright dependency.
    page.screenshot(path=str(output_path), full_page=True)  # type: ignore[attr-defined]
    return output_path


def check_page_risk(page: object) -> RiskCheckResult:
    content = page.content()  # type: ignore[attr-defined]
    return detect_risk_text(content)


def navigate_export_page(page: object, screenshots_dir: Path) -> None:
    page.get_by_text("商品", exact=False).click(timeout=NAV_TIMEOUT_MS)  # type: ignore[attr-defined]
    page.get_by_text("商机中心", exact=False).click(timeout=NAV_TIMEOUT_MS)  # type: ignore[attr-defined]
    page.get_by_text("潜力爆品", exact=False).click(timeout=NAV_TIMEOUT_MS)  # type: ignore[attr-defined]
    page.get_by_text("7天", exact=False).click(timeout=NAV_TIMEOUT_MS)  # type: ignore[attr-defined]
    save_named_screenshot(page, screenshots_dir, "STEP_navigation_ready.png")


def select_category(page: object, category: str) -> None:
    page.get_by_text(category, exact=False).click(timeout=NAV_TIMEOUT_MS)  # type: ignore[attr-defined]
