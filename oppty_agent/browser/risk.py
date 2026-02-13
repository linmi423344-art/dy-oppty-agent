from __future__ import annotations

DEFAULT_RISK_KEYWORDS = ["风险", "环境存在风险", "操作频次", "安全验证", "验证码"]


def find_risk_keywords(text: str, keywords: list[str] | None = None) -> list[str]:
    haystack = text or ""
    needles = keywords or DEFAULT_RISK_KEYWORDS
    return [keyword for keyword in needles if keyword and keyword in haystack]


def has_risk(text: str, keywords: list[str] | None = None) -> bool:
    return bool(find_risk_keywords(text=text, keywords=keywords))
