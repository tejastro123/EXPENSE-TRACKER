"""
ExpenseFlow X - Analytics Service
Advanced financial analytics: trends, heatmaps, category analysis, Sankey data
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uvicorn

from app.core.config import settings
from app.core.database import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Analytics Service started")
    yield
    print("🔴 Analytics Service shutting down...")


app = FastAPI(
    title="ExpenseFlow X — Analytics Service",
    description="Advanced Financial Analytics & Business Intelligence",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "analytics-service"}


# ── Inline Analytics Routes ───────────────────────────────────────────────────────

from fastapi import APIRouter
from datetime import date, timedelta
from decimal import Decimal
import uuid, random

router = APIRouter(prefix="/api/v1/analytics")


@router.get("/spending-heatmap")
async def spending_heatmap(
    user_id: str,
    year: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Day-by-day spending intensity heatmap (GitHub contribution style)"""
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    
    # In production: query from DB grouped by date
    # Demo: synthetic data
    data = {}
    current = start
    while current <= end:
        if random.random() > 0.3:  # ~70% of days have spending
            data[current.isoformat()] = round(random.uniform(100, 5000), 2)
        current += timedelta(days=1)

    return {
        "user_id": user_id,
        "year": year,
        "heatmap_data": data,
        "total_spent": sum(data.values()),
        "avg_daily_spent": sum(data.values()) / len(data) if data else 0,
        "max_single_day": max(data.values()) if data else 0,
        "active_days": len(data),
    }


@router.get("/category-radar")
async def category_radar(user_id: str, months: int = Query(3, ge=1, le=12)):
    """Category spending radar chart data"""
    categories = [
        "Food", "Transport", "Entertainment", "Health",
        "Shopping", "Utilities", "Education", "Travel"
    ]
    current_values = [random.randint(2000, 15000) for _ in categories]
    budget_values = [v * random.uniform(0.8, 1.3) for v in current_values]

    return {
        "categories": categories,
        "current_period": current_values,
        "budget": [round(v, 2) for v in budget_values],
        "comparison_period": [round(v * random.uniform(0.7, 1.2), 2) for v in current_values],
    }


@router.get("/sankey")
async def sankey_data(user_id: str, month: int = Query(...), year: int = Query(...)):
    """Income → Category flow for Sankey diagram"""
    return {
        "nodes": [
            {"id": "income", "label": "Income", "value": 80000},
            {"id": "food", "label": "Food & Dining", "value": 12000},
            {"id": "transport", "label": "Transport", "value": 5000},
            {"id": "utilities", "label": "Utilities", "value": 4000},
            {"id": "entertainment", "label": "Entertainment", "value": 3000},
            {"id": "health", "label": "Health", "value": 2500},
            {"id": "shopping", "label": "Shopping", "value": 8000},
            {"id": "investments", "label": "Investments", "value": 15000},
            {"id": "savings", "label": "Savings", "value": 10500},
            {"id": "other", "label": "Other", "value": 20000},
        ],
        "links": [
            {"source": "income", "target": "food", "value": 12000},
            {"source": "income", "target": "transport", "value": 5000},
            {"source": "income", "target": "utilities", "value": 4000},
            {"source": "income", "target": "entertainment", "value": 3000},
            {"source": "income", "target": "health", "value": 2500},
            {"source": "income", "target": "shopping", "value": 8000},
            {"source": "income", "target": "investments", "value": 15000},
            {"source": "income", "target": "savings", "value": 10500},
            {"source": "income", "target": "other", "value": 20000},
        ],
    }


@router.get("/trend-analysis")
async def trend_analysis(user_id: str, months: int = Query(12, ge=1, le=24)):
    """Monthly spending vs income trend over time"""
    results = []
    base = date.today().replace(day=1)
    for i in range(months - 1, -1, -1):
        month_start = (base - timedelta(days=30 * i)).replace(day=1)
        income = random.uniform(70000, 90000)
        expenses = random.uniform(45000, 70000)
        savings = income - expenses
        results.append({
            "month": month_start.strftime("%b %Y"),
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "savings": round(savings, 2),
            "savings_rate": round((savings / income) * 100, 1),
        })
    return {"user_id": user_id, "months": months, "data": results}


@router.get("/net-worth")
async def net_worth(user_id: str):
    """Net worth breakdown: assets vs liabilities"""
    return {
        "user_id": user_id,
        "assets": {
            "bank_savings": 250000,
            "investments": 350000,
            "fixed_deposits": 100000,
            "cash": 15000,
            "other_assets": 50000,
        },
        "liabilities": {
            "home_loan": 0,
            "car_loan": 50000,
            "personal_loan": 0,
            "credit_card_debt": 12000,
        },
        "total_assets": 765000,
        "total_liabilities": 62000,
        "net_worth": 703000,
        "net_worth_change_pct": 4.2,
        "calculated_at": date.today().isoformat(),
    }


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
