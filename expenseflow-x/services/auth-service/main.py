"""
ExpenseFlow X - Auth Service
Handles: JWT auth, OAuth2, MFA/2FA, RBAC, session management
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

from app.core.config import settings
from app.core.database import engine, Base
from app.core.redis_client import redis_client
from app.api.v1 import auth, users, oauth, mfa, sessions
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    await redis_client.ping()
    print(f"✅ Auth Service started — {settings.APP_NAME} v{settings.APP_VERSION}")
    yield
    # Shutdown
    await redis_client.close()
    print("🔴 Auth Service shutting down...")


app = FastAPI(
    title="ExpenseFlow X — Auth Service",
    description="Authentication, Authorization & Identity Management",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls=60, period=60)

# ── Routers ─────────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(oauth.router, prefix="/api/v1/oauth", tags=["OAuth2"])
app.include_router(mfa.router, prefix="/api/v1/mfa", tags=["MFA/2FA"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": settings.APP_VERSION,
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True, workers=1)
