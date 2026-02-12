"""Selection scoring placeholders."""

from __future__ import annotations

from pydantic import BaseModel


class ScoreResult(BaseModel):
    score: float
