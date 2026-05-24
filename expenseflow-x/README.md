# 🚀 ExpenseFlow X — AI-Native Fintech Intelligence Platform

> **Not an expense tracker. An AI-powered financial operating system.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)](https://typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-red)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🧠 What is ExpenseFlow X?

ExpenseFlow X is an **enterprise-grade, AI-native fintech platform** combining the intelligence of modern ML systems with the UX polish of world-class financial products.

Think: **Stripe + Plaid + YNAB + Robinhood + OpenAI** — all in one platform.

---

## 🏗️ Architecture Overview

```
Web / Mobile App
      │
API Gateway (gateway-service)
      │
┌─────┴──────────────────────────┐
│         FastAPI Backend         │
└─────────────────────────────────┘
  │        │         │        │
Auth    Finance    AI/ML   Notification
Service  Engine   Engine    Service
  │        │         │        │
  └────────┴─────────┴────────┘
                │
     Event Streaming (Kafka/Redis)
                │
    PostgreSQL + Pinecone (Vector DB)
                │
       Analytics Warehouse
```

---

## 📦 Project Structure

```
expenseflow-x/
├── apps/
│   ├── frontend/          # Next.js 14 + TypeScript + TailwindCSS
│   ├── admin-dashboard/   # Admin portal (Next.js)
│   └── analytics-portal/  # Streamlit AI analytics
│
├── services/
│   ├── auth-service/       # JWT, OAuth2, MFA, RBAC
│   ├── expense-service/    # Core expense CRUD + transactions
│   ├── ai-service/         # AI Copilot, RAG, predictions
│   ├── analytics-service/  # Financial analytics & scoring
│   ├── notification-service/ # Real-time alerts (WebSocket)
│   ├── gateway-service/    # API Gateway + rate limiting
│   └── admin-service/      # Admin APIs, audit, monitoring
│
├── infrastructure/
│   ├── docker/             # Docker configs per service
│   ├── kubernetes/         # K8s manifests
│   ├── terraform/          # IaC for cloud
│   └── nginx/              # Reverse proxy config
│
├── ml/
│   ├── models/             # Trained ML model artifacts
│   ├── pipelines/          # Feature engineering pipelines
│   ├── rag/                # RAG knowledge system
│   └── training/           # Training scripts
│
├── shared/                 # Shared schemas, utils, constants
├── docs/                   # API docs, architecture, deployment
├── tests/                  # Unit, integration, e2e tests
├── scripts/                # Dev, deployment, migration scripts
└── docker-compose.yml      # Full stack local orchestration
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- PostgreSQL 15
- Redis 7

### 1. Clone & Setup
```bash
git clone https://github.com/your-org/expenseflow-x.git
cd expenseflow-x
cp .env.example .env
```

### 2. Start All Services
```bash
docker-compose up -d
```

### 3. Run Migrations
```bash
cd services/expense-service
alembic upgrade head
```

### 4. Start Frontend
```bash
cd apps/frontend
npm install
npm run dev
```

### 5. Access
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Gateway | http://localhost:8000 |
| Admin Dashboard | http://localhost:3001 |
| Analytics Portal | http://localhost:8501 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Grafana | http://localhost:3030 |
| Prometheus | http://localhost:9090 |

---

## 🤖 AI Modules

| Module | Description | Models Used |
|--------|-------------|-------------|
| Financial Prediction Engine | Forecast expenses, cash flow, savings | XGBoost, LSTM, Prophet |
| AI Copilot | Conversational finance assistant | GPT-4 + RAG |
| Fraud Detection | Anomaly detection on transactions | Isolation Forest, Autoencoders |
| Budget Optimizer | Smart budget auto-generation | Rule-based + ML |
| Health Scoring | Financial wellness score (0-100) | Weighted scoring model |
| RAG Knowledge | Finance Q&A from knowledge base | LangChain + Pinecone |
| Recommendation Engine | Personalized financial advice | Collaborative filtering |

---

## 🛡️ Security

- **Authentication:** JWT with rotation, OAuth2, MFA/2FA
- **Authorization:** Role-Based Access Control (RBAC)
- **Data:** bcrypt hashing, encryption-at-rest, secure cookies
- **API:** Rate limiting, CSRF protection, secure headers
- **Audit:** Full audit log trail for all mutations

---

## 🧪 Tech Stack

### Backend
- **Runtime:** Python 3.11, FastAPI, AsyncIO
- **ORM:** SQLAlchemy 2.0 + Alembic
- **Validation:** Pydantic v2
- **Queue:** Celery + Redis
- **Cache:** Redis

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** TailwindCSS + ShadCN UI
- **State:** Zustand
- **Animation:** Framer Motion

### Databases
- **Primary:** PostgreSQL 15
- **Cache:** Redis 7
- **Vector:** Pinecone

### DevOps
- **CI/CD:** GitHub Actions
- **Containers:** Docker + Docker Compose
- **Orchestration:** Kubernetes
- **Monitoring:** Prometheus + Grafana
- **Logging:** ELK Stack

---

## 📊 Enterprise Features

- ✅ Banking integrations (Plaid/Razorpay/Stripe)
- ✅ Subscription intelligence
- ✅ Smart invoice system with GST
- ✅ Tax intelligence engine
- ✅ Investment tracking (stocks, crypto, MF, SIPs)
- ✅ Goal-based financial planning
- ✅ Real-time fraud alerts
- ✅ Super admin portal

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
