from fastapi import APIRouter, Depends, Request
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/")
async def get_investments(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user_id
    return {"user_id": user_id, "investments": []}

@router.post("/")
async def create_investment(payload: dict, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user_id
    return {
        "id": "inv-1",
        "user_id": user_id,
        "asset_name": payload.get("asset_name"),
        "asset_class": payload.get("asset_class"),
        "units": payload.get("units"),
        "purchase_price": payload.get("purchase_price")
    }
