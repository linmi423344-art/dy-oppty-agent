from oppty_agent.browser.risk import detect_risk_text


def test_detect_risk_text_matches_keywords() -> None:
    result = detect_risk_text("页面提示环境存在风险，请完成验证码")

    assert result.blocked is True
    assert "环境存在风险" in result.matched_keywords
    assert "验证码" in result.matched_keywords


def test_detect_risk_text_when_safe() -> None:
    result = detect_risk_text("一切正常")

    assert result.blocked is False
    assert result.matched_keywords == []
