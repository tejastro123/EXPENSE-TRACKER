from fastapi import APIRouter, Depends, Request
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/")
async def get_subscriptions(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user_id
    return {"user_id": user_id, "subscriptions": []}

@router.post("/")
async def create_subscription(payload: dict, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user_id
    return {"id": "sub-1", "user_id": user_id, "name": payload.get("name"), "cost": payload.get("cost"), "billing_cycle": payload.get("billing_cycle")}
