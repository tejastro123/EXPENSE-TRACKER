# app/services/email_service.py
import logging

logger = logging.getLogger(__name__)

async def send_verification_email(email: str, user_id: str):
    logger.info(f"✉️ [MOCK] Sending verification email to {email} (User ID: {user_id})")
    # In a real setup, format HTML and send via SMTP
    # We can print the verification link to the console for easy development access:
    print(f"\n✉️  [DEV] Verification link: http://localhost:3000/auth/verify?token=verify_{user_id}\n")

async def send_password_reset_email(email: str, token: str):
    logger.info(f"✉️ [MOCK] Sending password reset email to {email} (Token: {token})")
    print(f"\n✉️  [DEV] Password reset link: http://localhost:3000/auth/reset-password?token={token}\n")
