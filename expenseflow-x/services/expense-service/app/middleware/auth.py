from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract headers injected by API Gateway
        request.state.user_id = request.headers.get("X-User-Id")
        request.state.user_role = request.headers.get("X-User-Role", "free")
        return await call_next(request)
