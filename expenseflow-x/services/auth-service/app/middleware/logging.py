# app/middleware/logging.py
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        print(f"📝 {request.method} {request.url.path} - {response.status_code} ({round(process_time * 1000, 2)}ms)")
        return response
