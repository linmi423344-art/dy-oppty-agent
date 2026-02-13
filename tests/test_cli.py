import json
from pathlib import Path

from oppty_agent.cli import DEFAULT_BASE_URL, AppConfig, load_config, run


def test_load_config_defaults_base_url_when_missing(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "username: test\npassword: test\nheadless: true\ndata_dir: data\n",
        encoding="utf-8",
    )

    parsed = load_config(cfg)

    assert parsed.base_url == DEFAULT_BASE_URL


def test_run_manifest_contains_base_url(tmp_path: Path) -> None:
    parsed = AppConfig(base_url="https://example.com/", data_dir=str(tmp_path))

    result = run(parsed, dry_run=True)
    data = json.loads(result.read_text(encoding="utf-8"))

    assert data["base_url"] == "https://example.com/"


def test_run_calls_injected_runner(tmp_path: Path) -> None:
    manifest_path = tmp_path / "run_manifest.json"
    manifest_path.write_text(json.dumps({"base_url": "https://example.com/"}), encoding="utf-8")

    def _fake_runner(config: AppConfig, run_id: str):
        class _Result:
            def __init__(self, path: Path):
                self.manifest_path = path

        return _Result(manifest_path)

    parsed = AppConfig(base_url="https://example.com/")

    result = run(parsed, runner=_fake_runner)
    data = json.loads(result.read_text(encoding="utf-8"))

    assert data["base_url"] == "https://example.com/"
