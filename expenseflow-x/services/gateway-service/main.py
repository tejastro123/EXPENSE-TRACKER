"""
ExpenseFlow X - API Gateway Service
Handles: request routing, rate limiting, auth validation, load balancing
"""
from contextlib import asynccontextmanager
from typing import Optional
import httpx
import time

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.redis_client import redis_client
from app.middleware.rate_limiter import RateLimiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
    print("✅ Gateway Service started")
    yield
    await app.state.http_client.aclose()
    print("🔴 Gateway Service shutting down...")


app = FastAPI(
    title="ExpenseFlow X — API Gateway",
    description="Central API Gateway with rate limiting, auth validation, and service routing",
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


# ── Service Registry ─────────────────────────────────────────────────────────────

SERVICE_REGISTRY = {
    "auth": settings.AUTH_SERVICE_URL,
    "expense": settings.EXPENSE_SERVICE_URL,
    "analytics": settings.ANALYTICS_SERVICE_URL,
    "ai": settings.AI_SERVICE_URL,
    "notification": settings.NOTIFICATION_SERVICE_URL,
    "admin": settings.ADMIN_SERVICE_URL,
}

# Routes that don't require authentication
PUBLIC_ROUTES = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/auth/verify-email",
    "/health",
    "/docs",
    "/openapi.json",
}

# Route to service mapping
ROUTE_MAP = {
    "/api/v1/auth": "auth",
    "/api/v1/users": "auth",
    "/api/v1/oauth": "auth",
    "/api/v1/mfa": "auth",
    "/api/v1/sessions": "auth",
    "/api/v1/expenses": "expense",
    "/api/v1/transactions": "expense",
    "/api/v1/budgets": "expense",
    "/api/v1/subscriptions": "expense",
    "/api/v1/goals": "expense",
    "/api/v1/receipts": "expense",
    "/api/v1/investments": "expense",
    "/api/v1/analytics": "analytics",
    "/api/v1/ai": "ai",
    "/api/v1/notifications": "notification",
    "/api/v1/admin": "admin",
}

rate_limiter = RateLimiter(redis_client, calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)


async def validate_token(request: Request) -> Optional[dict]:
    """Validate JWT with auth service, extract user claims"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        return None


def get_target_service(path: str) -> Optional[str]:
    """Determine target microservice from request path"""
    for prefix, service in ROUTE_MAP.items():
        if path.startswith(prefix):
            return service
    return None


@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    start_time = time.time()
    path = request.url.path

    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    is_limited = await rate_limiter.is_rate_limited(client_ip)
    if is_limited:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please slow down."},
            headers={"Retry-After": "60"},
        )

    # Auth check
    if path not in PUBLIC_ROUTES and not any(path.startswith(p) for p in PUBLIC_ROUTES):
        user_claims = await validate_token(request)
        if not user_claims and not path.startswith("/health"):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"},
            )
        if user_claims:
            # Inject user info into request headers for downstream services
            request.state.user_id = user_claims.get("sub")
            request.state.user_role = user_claims.get("role")

    response = await call_next(request)

    # Add timing header
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    response.headers["X-Gateway-Version"] = "1.0.0"

    return response


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_request(path: str, request: Request):
    """Forward requests to appropriate microservice"""
    full_path = f"/{path}"
    service_name = get_target_service(full_path)

    if not service_name:
        raise HTTPException(status_code=404, detail=f"No service found for route: {full_path}")

    service_url = SERVICE_REGISTRY.get(service_name)
    if not service_url:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {service_name}")

    # Build upstream request
    target_url = f"{service_url}{full_path}"
    params = dict(request.query_params)
    body = await request.body()

    headers = dict(request.headers)
    headers.pop("host", None)

    # Inject user context
    if hasattr(request.state, "user_id") and request.state.user_id:
        headers["X-User-Id"] = request.state.user_id
        headers["X-User-Role"] = getattr(request.state, "user_role", "free")

    try:
        client: httpx.AsyncClient = request.app.state.http_client
        upstream_response = await client.request(
            method=request.method,
            url=target_url,
            params=params,
            content=body,
            headers=headers,
        )
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            headers=dict(upstream_response.headers),
            media_type=upstream_response.headers.get("content-type"),
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"Cannot connect to {service_name}")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "gateway", "services": list(SERVICE_REGISTRY.keys())}


@app.get("/health/services")
async def services_health(request: Request):
    """Check health of all downstream services"""
    client: httpx.AsyncClient = request.app.state.http_client
    results = {}
    for name, url in SERVICE_REGISTRY.items():
        try:
            resp = await client.get(f"{url}/health", timeout=3.0)
            results[name] = {"status": "up", "code": resp.status_code}
        except Exception as e:
            results[name] = {"status": "down", "error": str(e)}
    return {"services": results}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
