"""State machine skeleton for browser automation."""

from __future__ import annotations

from pydantic import BaseModel


class StateTransition(BaseModel):
    source: str
    action: str
    target: str
