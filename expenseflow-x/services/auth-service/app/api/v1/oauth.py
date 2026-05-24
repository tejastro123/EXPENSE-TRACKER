# app/api/v1/oauth.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/login/google")
async def google_login():
    return {"message": "Redirecting to Google OAuth (Mock)"}

@router.get("/callback/google")
async def google_callback():
    return {"message": "Google authentication successful (Mock)"}
