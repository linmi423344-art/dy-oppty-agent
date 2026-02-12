"""Export parsing placeholders."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_export(path: Path) -> pd.DataFrame:
    """Placeholder reader for future xlsx exports."""
    return pd.read_excel(path)
