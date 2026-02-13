"""Artifact naming helpers for browser export flow."""

from pathlib import Path


RUN_MANIFEST_NAME = "run_manifest.json"
POST_EXPORT_SCREENSHOT = "post_export.png"


def stop_screenshot_path(run_dir: Path, reason: str) -> Path:
    return run_dir / f"STOP_{reason}.png"
