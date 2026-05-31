from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SalesRecord(BaseModel):
    """Initial row-level contract for analytics-ready sales data."""

    model_config = ConfigDict(extra="allow")

    sale_date: date
    sales_amount: Decimal = Field(ge=0)
    store_id: str | None = None
    item_id: str | None = None
    category: str | None = None
