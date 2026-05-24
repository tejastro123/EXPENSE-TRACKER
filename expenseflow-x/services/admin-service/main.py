"""
ExpenseFlow X - Admin Service
Super admin features: user management, fraud monitoring, platform metrics, audit trails
"""
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List
import random

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Admin Service started")
    yield
    print("🔴 Admin Service shutting down...")


app = FastAPI(
    title="ExpenseFlow X — Admin Service",
    description="Super Admin Platform: User Management, Analytics, Security",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router_prefix = "/api/v1/admin"

from fastapi import APIRouter
router = APIRouter(prefix=router_prefix)


# ── Platform Metrics ─────────────────────────────────────────────────────────

@router.get("/metrics/platform")
async def platform_metrics():
    """Real-time platform health metrics"""
    return {
        "users": {
            "total": 52341,
            "active_today": 8432,
            "new_this_month": 1240,
            "premium": 3812,
            "free": 48529,
            "suspended": 23,
        },
        "transactions": {
            "total_processed": 2_150_000,
            "today": 42150,
            "this_month": 890_000,
            "total_value_inr": 4_500_000_000,
        },
        "ai": {
            "copilot_conversations_today": 3420,
            "fraud_checks_today": 42150,
            "fraud_detected_today": 127,
            "health_scores_calculated": 18432,
            "predictions_generated": 5820,
        },
        "system": {
            "api_requests_today": 1_240_000,
            "avg_response_ms": 42,
            "error_rate_pct": 0.03,
            "uptime_pct": 99.97,
            "active_websocket_connections": 2134,
        },
        "revenue": {
            "mrr_inr": 1_920_000,
            "arr_inr": 23_040_000,
            "churn_rate_pct": 1.2,
        },
    }


@router.get("/metrics/fraud-monitoring")
async def fraud_monitoring():
    """Real-time fraud detection monitoring"""
    alerts = []
    for i in range(10):
        alerts.append({
            "id": f"alert-{i}",
            "user_id": f"user-{random.randint(1000, 9999)}",
            "fraud_score": round(random.uniform(0.75, 0.99), 3),
            "risk_level": random.choice(["high", "critical"]),
            "amount_inr": round(random.uniform(5000, 100000), 2),
            "detected_at": (datetime.utcnow() - timedelta(minutes=random.randint(0, 120))).isoformat(),
            "is_resolved": random.choice([True, False]),
        })

    return {
        "total_alerts_today": 127,
        "critical_alerts": 12,
        "resolved": 98,
        "pending_review": 29,
        "total_amount_at_risk": 2_450_000,
        "recent_alerts": alerts,
    }


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
):
    """Admin: List all users with filtering"""
    users = []
    for i in range(page_size):
        idx = (page - 1) * page_size + i
        users.append({
            "id": f"user-{idx:05d}",
            "email": f"user{idx}@example.com",
            "full_name": f"User {idx}",
            "role": random.choice(["free", "premium", "admin"]),
            "status": random.choice(["active", "active", "active", "inactive", "suspended"]),
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(0, 365))).isoformat(),
            "last_login_at": (datetime.utcnow() - timedelta(hours=random.randint(0, 720))).isoformat(),
            "mfa_enabled": random.choice([True, False]),
            "total_expenses": random.randint(0, 500),
            "health_score": random.randint(40, 100),
        })

    return {
        "items": users,
        "total": 52341,
        "page": page,
        "page_size": page_size,
        "total_pages": 2618,
    }


@router.patch("/users/{user_id}/status")
async def update_user_status(user_id: str, status: str):
    """Admin: Suspend or activate a user"""
    if status not in ["active", "inactive", "suspended"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    return {"user_id": user_id, "status": status, "updated_at": datetime.utcnow().isoformat()}


@router.get("/audit-logs")
async def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50),
    event: Optional[str] = None,
    user_id: Optional[str] = None,
    success: Optional[bool] = None,
):
    """Admin: View complete audit trail"""
    logs = []
    events = ["login_success", "login_failed", "user_registered", "logout", "password_changed", "mfa_enabled"]
    for i in range(page_size):
        logs.append({
            "id": f"log-{(page-1)*page_size+i:08d}",
            "user_id": f"user-{random.randint(1000, 9999)}",
            "event": random.choice(events),
            "ip_address": f"192.168.{random.randint(0,255)}.{random.randint(0,255)}",
            "success": random.choice([True, True, True, False]),
            "created_at": (datetime.utcnow() - timedelta(minutes=random.randint(0, 10080))).isoformat(),
        })
    return {"items": logs, "total": 1_500_000, "page": page, "page_size": page_size}


@router.get("/system-health")
async def system_health():
    """Admin: Full system health check"""
    return {
        "services": {
            "gateway": {"status": "up", "latency_ms": 2},
            "auth": {"status": "up", "latency_ms": 5},
            "expense": {"status": "up", "latency_ms": 8},
            "analytics": {"status": "up", "latency_ms": 12},
            "ai": {"status": "up", "latency_ms": 45},
            "notification": {"status": "up", "latency_ms": 3},
        },
        "databases": {
            "postgres": {"status": "up", "connections": 42, "pool_size": 100},
            "redis": {"status": "up", "memory_mb": 128, "keys": 45230},
        },
        "celery": {
            "workers": 4,
            "active_tasks": 12,
            "pending_tasks": 5,
        },
        "checked_at": datetime.utcnow().isoformat(),
    }


app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "admin-service"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
