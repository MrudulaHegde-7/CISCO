"""Pydantic request and response schemas for alerts."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class AlertCreate(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    title: str
    severity: Literal["critical", "warning", "info"]
    source: str
    metric_name: str
    metric_value: float
    threshold: float


class AlertOut(AlertCreate):
    model_config = ConfigDict(from_attributes=True, allow_inf_nan=False)

    id: int
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def restore_utc_timezone(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class ExplainResponse(BaseModel):
    alert_id: int
    explanation: str
    generated_at: datetime