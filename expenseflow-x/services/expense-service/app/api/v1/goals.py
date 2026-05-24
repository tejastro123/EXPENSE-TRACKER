from fastapi import APIRouter, Depends, Request
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/")
async def get_goals(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user_id
    return {"user_id": user_id, "goals": []}

@router.post("/")
async def create_goal(payload: dict, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user_id
    return {"id": "goal-1", "user_id": user_id, "name": payload.get("name"), "target_amount": payload.get("target_amount"), "current_amount": payload.get("current_amount")}
