from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ForecastingSalesRecord(BaseModel):
    """Row-level contract for the department-week forecasting dataset."""

    model_config = ConfigDict(extra="allow")

    store_id: int = Field(gt=0)
    department: int = Field(gt=0)
    sale_date: date
    weekly_sales: Decimal = Field(ge=0)
    sales_amount: Decimal = Field(ge=0)
    store_type: str
    store_size: int = Field(gt=0)
    region: str
    temperature: Decimal
    fuel_price: Decimal = Field(ge=0)
    markdown_total: Decimal = Field(ge=0)
    cpi: Decimal = Field(ge=0)
    unemployment: Decimal = Field(ge=0)
    is_holiday: bool
    holiday_name: str
    season: str
    year: int = Field(ge=2000)
    quarter: int = Field(ge=1, le=4)
    month: int = Field(ge=1, le=12)
    week_of_year: int = Field(ge=1, le=53)
    day_of_week: int = Field(ge=0, le=6)


class StoreWeeklySalesRecord(BaseModel):
    """Row-level contract for the store-week aggregate dataset."""

    model_config = ConfigDict(extra="allow")

    store_id: int = Field(gt=0)
    sale_date: date
    weekly_sales: Decimal = Field(ge=0)
    sales_amount: Decimal = Field(ge=0)
    department_count: int = Field(gt=0)
    is_holiday: bool
    markdown_total: Decimal = Field(ge=0)
    store_type: str
    store_size: int = Field(gt=0)
    region: str
    holiday_name: str
    season: str
    year: int = Field(ge=2000)
    quarter: int = Field(ge=1, le=4)
    month: int = Field(ge=1, le=12)
    week_of_year: int = Field(ge=1, le=53)
    day_of_week: int = Field(ge=0, le=6)


SalesRecord = ForecastingSalesRecord
