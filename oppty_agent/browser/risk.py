from __future__ import annotations

from dataclasses import dataclass

RISK_KEYWORDS = ["风险", "环境存在风险", "操作频次", "安全验证", "验证码"]


@dataclass
class RiskCheckResult:
    blocked: bool
    matched_keywords: list[str]


def detect_risk_text(content: str) -> RiskCheckResult:
    matched = [keyword for keyword in RISK_KEYWORDS if keyword in content]
    return RiskCheckResult(blocked=bool(matched), matched_keywords=matched)
