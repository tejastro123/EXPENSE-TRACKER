# app/middleware/rate_limit.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 60, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean up old clients
        self.clients = {ip: times for ip, times in self.clients.items() if times and times[-1] > now - self.period}
        
        if client_ip not in self.clients:
            self.clients[client_ip] = []
            
        # Filter calls in period window
        self.clients[client_ip] = [t for t in self.clients[client_ip] if t > now - self.period]
        
        if len(self.clients[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."}
            )
            
        self.clients[client_ip].append(now)
        return await call_next(request)
