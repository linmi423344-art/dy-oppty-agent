from oppty_agent.browser.manifest import build_category_entry, build_run_manifest
from oppty_agent.browser.risk import match_risk_reason


def test_build_category_entry_shape() -> None:
    entry = build_category_entry("美妆")
    assert entry["category"] == "美妆"
    assert entry["status"] == "PENDING"
    assert isinstance(entry["screenshots"], list)


def test_build_run_manifest_contains_required_sections() -> None:
    manifest = build_run_manifest("run123", "https://example.com", "潜力爆品", "7天", ["美妆"])
    assert manifest["run_id"] == "run123"
    assert manifest["module"] == "潜力爆品"
    assert manifest["window"] == "7天"
    assert manifest["categories"] == ["美妆"]
    assert manifest["per_category"] == []


def test_match_risk_reason_keywords() -> None:
    assert match_risk_reason("当前环境存在风险，请完成安全验证") in {"风险", "环境存在风险"}
    assert match_risk_reason("请输入验证码") == "验证码"
    assert match_risk_reason("normal content") is None
