"""Expense Service - Expenses CRUD Router"""
from typing import List, Optional
from datetime import date
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from pydantic import BaseModel, Field
from decimal import Decimal

from app.core.database import get_db
from app.models.financial import Expense, ExpenseCategory, TransactionType

router = APIRouter()


# ── Schemas ─────────────────────────────────────────────────────────────────────

class ExpenseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    category: ExpenseCategory
    sub_category: Optional[str] = None
    tags: Optional[List[str]] = None
    transaction_type: TransactionType = TransactionType.DEBIT
    merchant_name: Optional[str] = None
    location: Optional[str] = None
    expense_date: date
    is_recurring: bool = False
    recurrence_type: Optional[str] = None
    is_tax_deductible: bool = False
    account_id: Optional[uuid.UUID] = None


class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    category: Optional[ExpenseCategory] = None
    tags: Optional[List[str]] = None
    merchant_name: Optional[str] = None
    location: Optional[str] = None
    expense_date: Optional[date] = None
    is_tax_deductible: Optional[bool] = None


class ExpenseResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str]
    amount: Decimal
    currency: str
    category: str
    transaction_type: str
    merchant_name: Optional[str]
    location: Optional[str]
    expense_date: date
    is_recurring: bool
    is_tax_deductible: bool
    is_flagged: bool
    fraud_score: Optional[float]
    created_at: date


class ExpenseListResponse(BaseModel):
    items: List[ExpenseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Routes ───────────────────────────────────────────────────────────────────────

@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    # current_user_id injected by gateway auth header
    x_user_id: Optional[str] = None,
):
    """Create a new expense"""
    expense = Expense(
        user_id=uuid.UUID(x_user_id) if x_user_id else uuid.uuid4(),
        **payload.model_dump()
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


@router.get("/", response_model=ExpenseListResponse)
async def list_expenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[ExpenseCategory] = None,
    transaction_type: Optional[TransactionType] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    search: Optional[str] = None,
    sort_by: str = Query("expense_date", enum=["expense_date", "amount", "created_at"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    db: AsyncSession = Depends(get_db),
    x_user_id: Optional[str] = None,
):
    """List expenses with filtering, searching, pagination"""
    user_id = uuid.UUID(x_user_id) if x_user_id else None
    filters = []
    if user_id:
        filters.append(Expense.user_id == user_id)
    if category:
        filters.append(Expense.category == category)
    if transaction_type:
        filters.append(Expense.transaction_type == transaction_type)
    if date_from:
        filters.append(Expense.expense_date >= date_from)
    if date_to:
        filters.append(Expense.expense_date <= date_to)
    if min_amount:
        filters.append(Expense.amount >= min_amount)
    if max_amount:
        filters.append(Expense.amount <= max_amount)
    if search:
        filters.append(Expense.title.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(Expense).where(and_(*filters))
    total = (await db.execute(count_query)).scalar()

    order_col = getattr(Expense, sort_by)
    order = desc(order_col) if sort_order == "desc" else order_col

    query = (
        select(Expense)
        .where(and_(*filters))
        .order_by(order)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    expenses = result.scalars().all()

    return ExpenseListResponse(
        items=expenses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(expense_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get single expense by ID"""
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: uuid.UUID,
    payload: ExpenseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Partially update expense"""
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(expense, key, value)

    await db.commit()
    await db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete expense"""
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    await db.delete(expense)
    await db.commit()


@router.get("/summary/monthly")
async def monthly_summary(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    x_user_id: Optional[str] = None,
):
    """Monthly spending summary by category"""
    user_id = uuid.UUID(x_user_id) if x_user_id else None
    query = (
        select(
            Expense.category,
            func.sum(Expense.amount).label("total"),
            func.count(Expense.id).label("count"),
            func.avg(Expense.amount).label("average"),
        )
        .where(
            and_(
                Expense.user_id == user_id,
                func.extract("year", Expense.expense_date) == year,
                func.extract("month", Expense.expense_date) == month,
                Expense.transaction_type == TransactionType.DEBIT,
            )
        )
        .group_by(Expense.category)
        .order_by(desc("total"))
    )
    result = await db.execute(query)
    rows = result.all()
    return {
        "year": year,
        "month": month,
        "summary": [
            {
                "category": row.category,
                "total": float(row.total),
                "count": row.count,
                "average": float(row.average),
            }
            for row in rows
        ],
        "total_spent": sum(float(r.total) for r in rows),
    }
