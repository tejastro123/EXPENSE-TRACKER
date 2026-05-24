"""
AI Service - Fraud Detection System
Uses Isolation Forest + Statistical anomaly detection to flag suspicious transactions
"""
import uuid
import numpy as np
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

from app.core.config import settings

router = APIRouter()

# ── Schemas ─────────────────────────────────────────────────────────────────────

class Transaction(BaseModel):
    id: str
    amount: float
    category: str
    merchant_name: Optional[str] = None
    hour_of_day: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    user_avg_amount: Optional[float] = None
    user_std_amount: Optional[float] = None
    days_since_last_transaction: Optional[float] = None
    is_international: bool = False


class FraudCheckRequest(BaseModel):
    transaction: Transaction
    user_id: str


class FraudCheckResponse(BaseModel):
    transaction_id: str
    fraud_score: float  # 0.0 = clean, 1.0 = highly suspicious
    is_suspicious: bool
    risk_level: str  # low, medium, high, critical
    risk_factors: List[str]
    recommendation: str
    checked_at: datetime


class BatchFraudCheckRequest(BaseModel):
    transactions: List[Transaction]
    user_id: str


# ── Fraud Detector ───────────────────────────────────────────────────────────────

class FraudDetector:
    """
    Multi-model fraud detection:
    1. Isolation Forest — statistical anomaly detection
    2. Rule-based heuristics — hardcoded financial fraud patterns
    3. Z-score statistical analysis — deviation from user's normal behavior
    """

    MODEL_PATH = "/app/models/cache/fraud_isolation_forest.joblib"
    SCALER_PATH = "/app/models/cache/fraud_scaler.joblib"

    def __init__(self):
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self._load_or_initialize_model()

    def _load_or_initialize_model(self):
        """Load existing model or create a fresh untrained one"""
        if os.path.exists(self.MODEL_PATH) and os.path.exists(self.SCALER_PATH):
            self.model = joblib.load(self.MODEL_PATH)
            self.scaler = joblib.load(self.SCALER_PATH)
        else:
            self.model = IsolationForest(
                n_estimators=200,
                contamination=0.05,
                random_state=42,
                max_features=1.0,
            )
            self.scaler = StandardScaler()

    def _extract_features(self, txn: Transaction) -> np.ndarray:
        """Extract numerical features from transaction for ML scoring"""
        # Normalize amount deviation
        if txn.user_avg_amount and txn.user_std_amount and txn.user_std_amount > 0:
            z_score = (txn.amount - txn.user_avg_amount) / txn.user_std_amount
        else:
            z_score = 0.0

        features = np.array([[
            txn.amount,
            txn.hour_of_day,
            txn.day_of_week,
            z_score,
            float(txn.is_international),
            txn.days_since_last_transaction or 1.0,
            txn.amount / (txn.user_avg_amount or txn.amount),  # amount ratio
        ]])
        return features

    def _apply_rules(self, txn: Transaction) -> List[str]:
        """Hardcoded fraud heuristics"""
        risk_factors = []

        # Large amount
        if txn.amount > 50000:
            risk_factors.append("Unusually large transaction amount (>₹50,000)")

        # Late night transaction (11pm - 4am)
        if txn.hour_of_day >= 23 or txn.hour_of_day <= 4:
            risk_factors.append("Transaction at unusual hours (late night/early morning)")

        # International transaction
        if txn.is_international:
            risk_factors.append("International transaction detected")

        # Massive deviation from user's norm
        if txn.user_avg_amount and txn.user_std_amount:
            z_score = abs((txn.amount - txn.user_avg_amount) / max(txn.user_std_amount, 1))
            if z_score > 3:
                risk_factors.append(f"Amount is {z_score:.1f}σ above your normal spending")

        # Very rapid succession (< 1 day since last transaction of similar amount)
        if txn.days_since_last_transaction and txn.days_since_last_transaction < 0.1:
            risk_factors.append("Very rapid successive transactions")

        return risk_factors

    def _compute_statistical_score(self, txn: Transaction) -> float:
        """Z-score based statistical anomaly score (0.0 - 1.0)"""
        if not txn.user_avg_amount or not txn.user_std_amount or txn.user_std_amount == 0:
            return 0.2
        z_score = abs((txn.amount - txn.user_avg_amount) / txn.user_std_amount)
        # Sigmoid transform: maps z_score to 0-1
        return float(1 / (1 + np.exp(-0.5 * (z_score - 2))))

    def score_transaction(self, txn: Transaction) -> FraudCheckResponse:
        """Run all fraud detection models and aggregate"""
        features = self._extract_features(txn)
        risk_factors = self._apply_rules(txn)
        statistical_score = self._compute_statistical_score(txn)

        # Isolation Forest score (-1 = anomaly, 1 = normal)
        ml_score = 0.3  # default if model not trained
        try:
            scaled = self.scaler.transform(features)
            raw_score = self.model.score_samples(scaled)[0]
            # Map to 0-1 (lower score = more anomalous)
            ml_score = max(0.0, min(1.0, 1.0 - (raw_score + 0.5)))
        except Exception:
            pass

        # Weighted ensemble score
        rule_score = min(1.0, len(risk_factors) * 0.25)
        fraud_score = (0.4 * ml_score + 0.35 * statistical_score + 0.25 * rule_score)
        fraud_score = max(0.0, min(1.0, fraud_score))

        # Risk classification
        if fraud_score < 0.3:
            risk_level = "low"
            recommendation = "Transaction appears normal. No action needed."
        elif fraud_score < 0.5:
            risk_level = "medium"
            recommendation = "Some unusual patterns detected. Monitor this transaction."
        elif fraud_score < 0.75:
            risk_level = "high"
            recommendation = "High risk transaction. Consider verifying with your bank."
        else:
            risk_level = "critical"
            recommendation = "⚠️ CRITICAL: Potential fraud detected! Contact your bank immediately."

        return FraudCheckResponse(
            transaction_id=txn.id,
            fraud_score=round(fraud_score, 4),
            is_suspicious=fraud_score >= settings.FRAUD_THRESHOLD,
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendation=recommendation,
            checked_at=datetime.utcnow(),
        )


# Global detector instance (lazy-loaded)
_detector: Optional[FraudDetector] = None


def get_detector() -> FraudDetector:
    global _detector
    if _detector is None:
        _detector = FraudDetector()
    return _detector


# ── Routes ───────────────────────────────────────────────────────────────────────

@router.post("/check", response_model=FraudCheckResponse)
async def check_fraud(payload: FraudCheckRequest, background_tasks: BackgroundTasks):
    """Run fraud detection on a single transaction"""
    detector = get_detector()
    result = detector.score_transaction(payload.transaction)

    if result.is_suspicious:
        # Async: store fraud alert in DB
        background_tasks.add_task(_store_fraud_alert, payload.user_id, result)

    return result


@router.post("/batch-check")
async def batch_check_fraud(payload: BatchFraudCheckRequest):
    """Run fraud detection on multiple transactions"""
    detector = get_detector()
    results = []
    for txn in payload.transactions:
        result = detector.score_transaction(txn)
        results.append(result)

    suspicious_count = sum(1 for r in results if r.is_suspicious)
    return {
        "total_checked": len(results),
        "suspicious_count": suspicious_count,
        "results": results,
    }


@router.get("/alerts/{user_id}")
async def get_fraud_alerts(user_id: str, limit: int = 20):
    """Get recent fraud alerts for a user"""
    # In production, query from DB
    return {"user_id": user_id, "alerts": [], "total": 0}


async def _store_fraud_alert(user_id: str, result: FraudCheckResponse):
    """Background task: persist fraud alert to database"""
    # Implementation: write to fraud_alerts table
    pass
