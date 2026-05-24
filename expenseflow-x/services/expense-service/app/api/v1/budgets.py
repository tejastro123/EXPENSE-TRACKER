from fastapi import APIRouter, Depends, Request
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/")
async def get_budgets(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user_id
    return {"user_id": user_id, "budgets": []}

@router.post("/")
async def create_budget(payload: dict, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user_id
    return {"id": "budget-1", "user_id": user_id, "category": payload.get("category"), "limit": payload.get("limit")}
