"""Selection report placeholders."""

from __future__ import annotations

from pathlib import Path


def write_report(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
