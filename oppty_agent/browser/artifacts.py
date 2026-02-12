"""Artifact management placeholders."""

from __future__ import annotations

from pathlib import Path


def ensure_artifact_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
