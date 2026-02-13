from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CategoryResult:
    category: str
    status: str
    download_path: str | None = None
    sha256: str | None = None
    screenshots: list[str] | None = None
    message: str = ""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_run_manifest(run_id: str, base_url: str, risk_flags: list[str] | None = None) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "created_at": utc_now_iso(),
        "base_url": base_url,
        "risk_flags": risk_flags or [],
        "categories": [],
    }


def add_category_result(manifest: dict[str, Any], result: CategoryResult) -> dict[str, Any]:
    manifest["categories"].append(
        {
            "category": result.category,
            "status": result.status,
            "download_path": result.download_path,
            "sha256": result.sha256,
            "screenshots": result.screenshots or [],
            "message": result.message,
        }
    )
    manifest["updated_at"] = utc_now_iso()
    return manifest
