from __future__ import annotations

from enum import Enum


class WorkerState(str, Enum):
    OPEN_BASE_URL = "open_base_url"
    OPEN_OPPORTUNITY_CENTER = "open_opportunity_center"
    OPEN_POTENTIAL_EXPLOSIVE_PRODUCTS = "open_potential_explosive_products"
    SET_RANGE_7_DAYS = "set_range_7_days"
    LOOP_CATEGORIES = "loop_categories"
    EXPORT = "export"
    DONE = "done"
