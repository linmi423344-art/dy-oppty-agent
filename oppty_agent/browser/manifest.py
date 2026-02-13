from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_run_manifest(run_id: str, base_url: str, module_label: str, window_label: str, categories: list[str]) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "started_at": utc_now_iso(),
        "finished_at": None,
        "base_url": base_url,
        "module": module_label,
        "window": window_label,
        "categories": categories,
        "risk_flags": [],
        "per_category": [],
    }


def build_category_entry(category_name: str) -> dict[str, Any]:
    return {
        "category": category_name,
        "status": "PENDING",
        "download_path": None,
        "sha256": None,
        "row_count": None,
        "screenshots": [],
        "error": None,
    }
