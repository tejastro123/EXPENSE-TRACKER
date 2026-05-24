"""Shared - Common Pydantic v2 Schemas used across all services"""
from datetime import datetime
from typing import Optional, Any, List, Generic, TypeVar
import uuid

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int):
        total_pages = max(1, (total + page_size - 1) // page_size)
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Any] = None
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime_seconds: Optional[float] = None
    dependencies: Optional[dict] = None


class AuditEvent(BaseModel):
    """Standardized audit event for all services"""
    event_type: str
    service: str
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str
    success: bool
    ip_address: Optional[str] = None
    metadata: Optional[dict] = None
    occurred_at: datetime = Field(default_factory=datetime.utcnow)


class CurrencyAmount(BaseModel):
    """Money with currency"""
    amount: float
    currency: str = "INR"

    def format(self) -> str:
        symbol = "₹" if self.currency == "INR" else self.currency
        return f"{symbol}{self.amount:,.2f}"


class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime

    def validate_range(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
