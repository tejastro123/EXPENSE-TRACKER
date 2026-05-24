# app/api/v1/mfa.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.api.v1.auth import get_current_user
import pyotp

router = APIRouter()

@router.post("/setup")
async def mfa_setup(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA already enabled")
    
    mfa_secret = pyotp.random_base32()
    current_user.mfa_secret = mfa_secret
    await db.commit()
    
    totp = pyotp.TOTP(mfa_secret)
    provisioning_url = totp.provisioning_uri(name=current_user.email, issuer_name="ExpenseFlowX")
    
    return {
        "secret": mfa_secret,
        "provisioning_url": provisioning_url
    }

@router.post("/verify")
async def mfa_verify(code: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not set up")
        
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid code")
        
    current_user.mfa_enabled = True
    await db.commit()
    return {"message": "MFA enabled successfully"}
