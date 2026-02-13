import json
from pathlib import Path

from oppty_agent.cli import DEFAULT_BASE_URL, load_config, run


def test_load_config_defaults_base_url_when_missing(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "username: test\npassword: test\nheadless: true\ndata_dir: data\n",
        encoding="utf-8",
    )

    parsed = load_config(cfg)

    assert parsed.base_url == DEFAULT_BASE_URL


def test_run_manifest_contains_base_url(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "username: test\npassword: test\nheadless: true\ndata_dir: test_data\n"
        "base_url: https://example.com/\n",
        encoding="utf-8",
    )
    parsed = load_config(cfg)

    manifest_path = run(parsed)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert data["base_url"] == "https://example.com/"
