# app/api/v1/sessions.py
from fastapi import APIRouter, Depends
from app.models.user import User
from app.api.v1.auth import get_current_user

router = APIRouter()

@router.get("/")
async def get_sessions(current_user: User = Depends(get_current_user)):
    return {
        "sessions": [
            {
                "id": "current",
                "ip_address": current_user.last_login_ip or "unknown",
                "last_active": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
                "is_current": True
            }
        ]
    }
