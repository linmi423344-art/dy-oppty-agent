from pathlib import Path

from oppty_agent.browser.manifest import CategoryResult, add_category_result, build_run_manifest, sha256_file


def test_manifest_builder_adds_category_result(tmp_path: Path) -> None:
    manifest = build_run_manifest(run_id="r1", base_url="https://example.com/")

    out = tmp_path / "x.csv"
    out.write_text("a,b\n1,2\n", encoding="utf-8")
    digest = sha256_file(out)

    add_category_result(
        manifest,
        CategoryResult(
            category="食品生鲜",
            status="success",
            download_path="食品生鲜/x.csv",
            sha256=digest,
            screenshots=["食品生鲜/post_export.png"],
        ),
    )

    assert manifest["categories"][0]["category"] == "食品生鲜"
    assert manifest["categories"][0]["sha256"] == digest
