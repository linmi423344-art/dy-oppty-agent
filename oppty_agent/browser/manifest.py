from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(run_id: str, base_url: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "risk_flags": [],
        "categories": [],
    }


def add_category_result(
    manifest: dict[str, Any],
    *,
    category: str,
    status: str,
    downloaded_file: str | None = None,
    sha256: str | None = None,
    error: str | None = None,
) -> None:
    item: dict[str, Any] = {
        "category": category,
        "status": status,
        "downloaded_file": downloaded_file,
        "sha256": sha256,
    }
    if error:
        item["error"] = error
    manifest["categories"].append(item)


def write_manifest(manifest: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
