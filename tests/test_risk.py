from oppty_agent.browser.risk import find_risk_keywords, has_risk


def test_find_risk_keywords_matches_multiple_terms() -> None:
    text = "页面提示环境存在风险，需要验证码"

    matches = find_risk_keywords(text)

    assert "环境存在风险" in matches
    assert "验证码" in matches
    assert has_risk(text)
