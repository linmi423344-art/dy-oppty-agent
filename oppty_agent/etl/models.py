"""ETL model placeholders."""

from __future__ import annotations

from pydantic import BaseModel


class OpportunityRecord(BaseModel):
    product_name: str
    category: str
