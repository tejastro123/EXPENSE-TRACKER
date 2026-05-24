# app/api/v1/users.py
from fastapi import APIRouter, Depends
from app.models.user import User
from app.api.v1.auth import get_current_user

router = APIRouter()

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone_number": current_user.phone_number,
        "role": current_user.role,
        "status": current_user.status,
        "mfa_enabled": current_user.mfa_enabled,
    }
