import json
from pathlib import Path

from oppty_agent.browser.manifest import add_category_result, build_manifest, compute_sha256, write_manifest


def test_manifest_builder_and_writer(tmp_path: Path) -> None:
    manifest = build_manifest("r1", "https://example.com/")
    sample = tmp_path / "sample.csv"
    sample.write_text("a,b\n1,2\n", encoding="utf-8")

    add_category_result(
        manifest,
        category="纸",
        status="downloaded",
        downloaded_file=str(sample),
        sha256=compute_sha256(sample),
    )

    out = tmp_path / "run_manifest.json"
    write_manifest(manifest, out)

    parsed = json.loads(out.read_text(encoding="utf-8"))
    assert parsed["run_id"] == "r1"
    assert parsed["base_url"] == "https://example.com/"
    assert parsed["categories"][0]["category"] == "纸"
    assert len(parsed["categories"][0]["sha256"]) == 64
