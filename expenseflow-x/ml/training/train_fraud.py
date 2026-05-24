"""
ML Training Pipeline — Fraud Detection Model
Trains Isolation Forest on expense transaction data
Run: python -m ml.training.train_fraud
"""
import argparse
import os
import pickle
import logging
from datetime import datetime
from typing import Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score
import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


def generate_synthetic_training_data(n_samples: int = 10000) -> pd.DataFrame:
    """Generate synthetic transaction data for training (replace with real DB query)"""
    np.random.seed(42)

    # Normal transactions
    normal = pd.DataFrame({
        "amount": np.random.exponential(1500, int(n_samples * 0.95)),
        "hour_of_day": np.random.randint(8, 22, int(n_samples * 0.95)),
        "day_of_week": np.random.randint(0, 7, int(n_samples * 0.95)),
        "z_score": np.random.normal(0, 1, int(n_samples * 0.95)),
        "is_international": np.random.choice([0, 1], int(n_samples * 0.95), p=[0.95, 0.05]),
        "days_since_last": np.random.exponential(2, int(n_samples * 0.95)),
        "amount_ratio": np.random.normal(1.0, 0.3, int(n_samples * 0.95)),
        "label": 0,  # Normal
    })

    # Anomalous transactions (fraud)
    fraud = pd.DataFrame({
        "amount": np.random.exponential(15000, int(n_samples * 0.05)),  # 10x normal
        "hour_of_day": np.random.choice([0, 1, 2, 3, 23], int(n_samples * 0.05)),  # Late night
        "day_of_week": np.random.randint(0, 7, int(n_samples * 0.05)),
        "z_score": np.random.normal(4, 1, int(n_samples * 0.05)),  # Far from mean
        "is_international": np.random.choice([0, 1], int(n_samples * 0.05), p=[0.3, 0.7]),  # More intl
        "days_since_last": np.random.uniform(0, 0.5, int(n_samples * 0.05)),  # Rapid succession
        "amount_ratio": np.random.normal(5.0, 1.5, int(n_samples * 0.05)),
        "label": 1,  # Fraud
    })

    df = pd.concat([normal, fraud], ignore_index=True).sample(frac=1, random_state=42)
    return df


def train_fraud_model(
    n_samples: int = 10000,
    contamination: float = 0.05,
    n_estimators: int = 200,
    output_dir: str = "ml/models",
) -> dict:
    """Train Isolation Forest fraud detection model"""
    logger.info("🚀 Starting fraud detection model training...")

    # Data
    logger.info("📊 Generating training data...")
    df = generate_synthetic_training_data(n_samples)
    feature_cols = ["amount", "hour_of_day", "day_of_week", "z_score", "is_international", "days_since_last", "amount_ratio"]
    X = df[feature_cols].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Preprocessing
    logger.info("⚙️ Fitting scaler...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Isolation Forest
    logger.info(f"🤖 Training Isolation Forest (n_estimators={n_estimators}, contamination={contamination})...")
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=42,
        max_features=1.0,
        n_jobs=-1,
    )
    model.fit(X_train_scaled)

    # Evaluate
    logger.info("📈 Evaluating model...")
    raw_scores = model.score_samples(X_test_scaled)
    # Convert to binary predictions (threshold at contamination percentile)
    threshold = np.percentile(raw_scores, contamination * 100)
    y_pred = (raw_scores < threshold).astype(int)

    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    metrics = {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "n_train_samples": len(X_train),
        "n_test_samples": len(X_test),
        "contamination": contamination,
        "n_estimators": n_estimators,
        "trained_at": datetime.utcnow().isoformat(),
    }

    logger.info(f"✅ Model metrics: Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}")

    # Save model artifacts
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "fraud_isolation_forest.joblib")
    scaler_path = os.path.join(output_dir, "fraud_scaler.joblib")
    metrics_path = os.path.join(output_dir, "fraud_metrics.json")

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    import json
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"💾 Model saved: {model_path}")
    logger.info(f"💾 Scaler saved: {scaler_path}")
    logger.info(f"📋 Metrics saved: {metrics_path}")

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train ExpenseFlow X Fraud Detection Model")
    parser.add_argument("--n-samples", type=int, default=10000, help="Training sample count")
    parser.add_argument("--contamination", type=float, default=0.05, help="Fraud rate (0-0.5)")
    parser.add_argument("--n-estimators", type=int, default=200, help="Number of trees")
    parser.add_argument("--output-dir", type=str, default="ml/models", help="Model output directory")
    args = parser.parse_args()

    metrics = train_fraud_model(
        n_samples=args.n_samples,
        contamination=args.contamination,
        n_estimators=args.n_estimators,
        output_dir=args.output_dir,
    )

    print("\n" + "="*60)
    print("🎉 FRAUD MODEL TRAINING COMPLETE")
    print("="*60)
    for k, v in metrics.items():
        print(f"  {k}: {v}")
