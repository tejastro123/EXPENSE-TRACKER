from fastapi import APIRouter, Depends, Request, UploadFile, File
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

router = APIRouter()

@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...), request: Request = None, db: AsyncSession = Depends(get_db)):
    # Mock upload logic
    receipt_id = str(uuid.uuid4())
    return {
        "id": receipt_id,
        "filename": file.filename,
        "url": f"https://mock-receipt-s3.amazonaws.com/{receipt_id}_{file.filename}",
        "status": "uploaded"
    }

@router.get("/")
async def get_receipts(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user_id if request else "dev"
    return {"user_id": user_id, "receipts": []}
