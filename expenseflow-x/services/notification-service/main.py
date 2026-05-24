"""
ExpenseFlow X - Notification Service
Handles: real-time WebSocket notifications, email, SMS, push notifications
"""
from contextlib import asynccontextmanager
from typing import Dict, Set, Optional
import asyncio
import json
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings
from app.core.redis_client import redis_client


# ── WebSocket Connection Manager ─────────────────────────────────────────────

class ConnectionManager:
    """Manages WebSocket connections per user"""
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        print(f"📡 WebSocket connected: user={user_id}, total={len(self.active_connections)}")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        """Send notification to all devices of a user"""
        if user_id not in self.active_connections:
            # Queue for when user reconnects (store in Redis)
            await redis_client.rpush(
                f"notifications:queue:{user_id}",
                json.dumps(message)
            )
            return

        dead_connections = set()
        for websocket in self.active_connections[user_id].copy():
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.add(websocket)

        for ws in dead_connections:
            self.disconnect(user_id, ws)

    async def broadcast(self, message: dict):
        """Broadcast to all connected users"""
        for user_id, connections in list(self.active_connections.items()):
            await self.send_to_user(user_id, message)

    @property
    def connected_count(self) -> int:
        return sum(len(conns) for conns in self.active_connections.values())


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Redis pub/sub listener for cross-service notifications
    asyncio.create_task(listen_for_events())
    print("✅ Notification Service started")
    yield
    print("🔴 Notification Service shutting down...")


app = FastAPI(
    title="ExpenseFlow X — Notification Service",
    description="Real-time WebSocket + Email + SMS Notifications",
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


# ── Schemas ──────────────────────────────────────────────────────────────────

class NotificationPayload(BaseModel):
    user_id: str
    type: str  # budget_alert, fraud_alert, goal_milestone, system
    title: str
    message: str
    data: Optional[dict] = None
    priority: str = "normal"  # low, normal, high, critical


class BroadcastPayload(BaseModel):
    type: str
    title: str
    message: str
    data: Optional[dict] = None


# ── WebSocket Routes ─────────────────────────────────────────────────────────

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications"""
    await manager.connect(user_id, websocket)

    # Send any queued notifications
    queued = await redis_client.lrange(f"notifications:queue:{user_id}", 0, -1)
    for msg_raw in queued:
        await websocket.send_text(msg_raw.decode())
    if queued:
        await redis_client.delete(f"notifications:queue:{user_id}")

    try:
        while True:
            # Keep connection alive with heartbeat
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            if data == "ping":
                await websocket.send_text("pong")
    except (WebSocketDisconnect, asyncio.TimeoutError):
        manager.disconnect(user_id, websocket)
    except Exception:
        manager.disconnect(user_id, websocket)


# ── REST Routes ──────────────────────────────────────────────────────────────

@app.post("/api/v1/notifications/send")
async def send_notification(payload: NotificationPayload):
    """Send real-time notification to a user"""
    notification = {
        "id": str(uuid.uuid4()),
        "type": payload.type,
        "title": payload.title,
        "message": payload.message,
        "data": payload.data or {},
        "priority": payload.priority,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }

    await manager.send_to_user(payload.user_id, notification)

    # For critical notifications, also send email
    if payload.priority == "critical":
        # asyncio.create_task(send_email_notification(payload))
        pass

    return {"sent": True, "notification_id": notification["id"]}


@app.post("/api/v1/notifications/broadcast")
async def broadcast_notification(payload: BroadcastPayload):
    """Broadcast system-wide notification"""
    await manager.broadcast({
        "id": str(uuid.uuid4()),
        "type": payload.type,
        "title": payload.title,
        "message": payload.message,
        "data": payload.data or {},
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    })
    return {"sent": True, "recipients": manager.connected_count}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "notification-service",
        "active_connections": manager.connected_count,
        "connected_users": len(manager.active_connections),
    }


# ── Redis Pub/Sub Listener ───────────────────────────────────────────────────

async def listen_for_events():
    """Listen to Redis pub/sub for cross-service notification events"""
    try:
        import aioredis
        sub = await aioredis.from_url(settings.REDIS_URL)
        pubsub = sub.pubsub()
        await pubsub.subscribe("notifications:realtime")

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    payload = json.loads(message["data"])
                    user_id = payload.get("user_id")
                    if user_id:
                        await manager.send_to_user(user_id, payload)
                    else:
                        await manager.broadcast(payload)
                except Exception:
                    pass
    except Exception as e:
        print(f"Redis pub/sub error: {e}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)
