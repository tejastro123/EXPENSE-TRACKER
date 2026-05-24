"""
ExpenseFlow X - Expense Service
Handles: CRUD for expenses, transactions, budgets, subscriptions, goals, receipts
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.api.v1 import expenses, transactions, budgets, subscriptions, goals, receipts, investments
from app.middleware.auth import JWTAuthMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"✅ Expense Service started")
    yield
    print(f"🔴 Expense Service shutting down...")


app = FastAPI(
    title="ExpenseFlow X — Expense Service",
    description="Core Financial Data Management",
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

app.include_router(expenses.router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["Budgets"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])
app.include_router(goals.router, prefix="/api/v1/goals", tags=["Goals"])
app.include_router(receipts.router, prefix="/api/v1/receipts", tags=["Receipts"])
app.include_router(investments.router, prefix="/api/v1/investments", tags=["Investments"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "expense-service"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
