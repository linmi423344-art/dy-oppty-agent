from __future__ import annotations

RISK_KEYWORDS = ["风险", "环境存在风险", "操作频次", "安全验证", "验证码", "captcha", "slider", "verify"]


def match_risk_reason(text: str) -> str | None:
    lowered = text.lower()
    for keyword in RISK_KEYWORDS:
        if keyword.lower() in lowered:
            return keyword
    return None


def detect_risk(page: object) -> str | None:
    """Detect risk/captcha indicators from page content."""
    try:
        content = page.content()
    except Exception:
        return None
    return match_risk_reason(content)
