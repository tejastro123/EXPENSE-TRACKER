from fastapi import APIRouter, Depends, Request
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime

router = APIRouter()

@router.get("/")
async def list_transactions(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user_id
    return {"user_id": user_id, "transactions": []}

@router.post("/")
async def create_transaction(payload: dict, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user_id
    return {"id": str(uuid.uuid4()), "user_id": user_id, "amount": payload.get("amount"), "category": payload.get("category"), "timestamp": datetime.utcnow().isoformat()}
