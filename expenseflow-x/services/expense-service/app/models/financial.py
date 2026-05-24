"""Expense Service - All Financial Models (SQLAlchemy 2.0)"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    String, Boolean, DateTime, Text, ForeignKey,
    Enum as SAEnum, Integer, Numeric, Date, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExpenseCategory(str, PyEnum):
    FOOD = "food"
    TRANSPORT = "transport"
    UTILITIES = "utilities"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    EDUCATION = "education"
    SHOPPING = "shopping"
    TRAVEL = "travel"
    RENT = "rent"
    INSURANCE = "insurance"
    INVESTMENT = "investment"
    TAXES = "taxes"
    SUBSCRIPTIONS = "subscriptions"
    INCOME = "income"
    SALARY = "salary"
    FREELANCE = "freelance"
    OTHER = "other"


class TransactionType(str, PyEnum):
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    REFUND = "refund"


class RecurrenceType(str, PyEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class GoalStatus(str, PyEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class InvestmentType(str, PyEnum):
    STOCK = "stock"
    CRYPTO = "crypto"
    MUTUAL_FUND = "mutual_fund"
    SIP = "sip"
    ETF = "etf"
    FIXED_DEPOSIT = "fixed_deposit"
    PPF = "ppf"
    NPS = "nps"
    REAL_ESTATE = "real_estate"
    GOLD = "gold"
    BONDS = "bonds"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    category: Mapped[ExpenseCategory] = mapped_column(SAEnum(ExpenseCategory), nullable=False)
    sub_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    # Transaction details
    transaction_type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), default=TransactionType.DEBIT)
    merchant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    merchant_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Recurrence
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_type: Mapped[Optional[RecurrenceType]] = mapped_column(SAEnum(RecurrenceType), nullable=True)
    recurrence_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Dates
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # AI enrichment
    ai_category_confidence: Mapped[Optional[float]] = mapped_column(Numeric(4, 3), nullable=True)
    is_tax_deductible: Mapped[bool] = mapped_column(Boolean, default=False)
    tax_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadata
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    fraud_score: Mapped[Optional[float]] = mapped_column(Numeric(4, 3), nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    receipt: Mapped[Optional["Receipt"]] = relationship(back_populates="expense", uselist=False)
    account: Mapped[Optional["Account"]] = relationship(back_populates="expenses")

    __table_args__ = (
        Index("ix_expenses_user_date", "user_id", "expense_date"),
        Index("ix_expenses_user_category", "user_id", "category"),
        Index("ix_expenses_amount", "amount"),
    )


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)  # savings, checking, credit, wallet
    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    bank_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_number_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    plaid_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    expenses: Mapped[List["Expense"]] = relationship(back_populates="account")


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[ExpenseCategory]] = mapped_column(SAEnum(ExpenseCategory), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    spent_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # monthly, weekly, yearly
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    alert_threshold_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=80.0)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    billing_cycle: Mapped[RecurrenceType] = mapped_column(SAEnum(RecurrenceType), nullable=False)
    next_billing_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=True)  # AI-detected usage
    cancellation_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_detected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # emergency, retirement, travel, etc.
    status: Mapped[GoalStatus] = mapped_column(SAEnum(GoalStatus), default=GoalStatus.ACTIVE)
    monthly_contribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    is_ai_planned: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_plan: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expense_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("expenses.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    expense: Mapped["Expense"] = relationship(back_populates="receipt")


class Investment(Base):
    __tablename__ = "investments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    symbol: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    investment_type: Mapped[InvestmentType] = mapped_column(SAEnum(InvestmentType), nullable=False)
    quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    buy_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    current_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    buy_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_invested: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    current_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    returns_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    platform: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
