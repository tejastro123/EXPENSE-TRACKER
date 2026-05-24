"""
ExpenseFlow X - AI Service
Handles: Financial AI Copilot, RAG, Fraud Detection, Predictions, Health Scoring, Budget Optimization
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.api.v1 import copilot, fraud, predictions, health_score, budget_optimizer, recommendations, rag
from app.celery_app import celery_app  # noqa: F401  — initializes Celery


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"✅ AI Service started — loading models...")
    # Lazy-load ML models on startup
    from app.ml.model_registry import ModelRegistry
    await ModelRegistry.initialize()
    print("🤖 ML models loaded")
    yield
    print("🔴 AI Service shutting down...")


app = FastAPI(
    title="ExpenseFlow X — AI Service",
    description="AI/ML Intelligence Layer: Copilot, Fraud, Predictions, Health Score",
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

app.include_router(copilot.router, prefix="/api/v1/ai/copilot", tags=["AI Copilot"])
app.include_router(rag.router, prefix="/api/v1/ai/rag", tags=["RAG Knowledge"])
app.include_router(fraud.router, prefix="/api/v1/ai/fraud", tags=["Fraud Detection"])
app.include_router(predictions.router, prefix="/api/v1/ai/predictions", tags=["Predictions"])
app.include_router(health_score.router, prefix="/api/v1/ai/health-score", tags=["Health Score"])
app.include_router(budget_optimizer.router, prefix="/api/v1/ai/budget", tags=["Budget Optimizer"])
app.include_router(recommendations.router, prefix="/api/v1/ai/recommendations", tags=["Recommendations"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ai-service"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
