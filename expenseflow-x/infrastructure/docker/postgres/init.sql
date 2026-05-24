-- ==============================================================================
-- ExpenseFlow X - PostgreSQL Initialization Script
-- Creates all database extensions and initial schema setup
-- ==============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- Full-text trigram search
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- GIN index for composite
CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- Encryption functions

-- ==============================================================================
-- ENUM TYPES
-- ==============================================================================

CREATE TYPE user_role AS ENUM ('super_admin', 'admin', 'premium', 'free');
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended', 'pending_verification');
CREATE TYPE transaction_type AS ENUM ('debit', 'credit', 'transfer', 'refund');
CREATE TYPE expense_category AS ENUM (
    'food', 'transport', 'utilities', 'entertainment', 'health',
    'education', 'shopping', 'travel', 'rent', 'insurance',
    'investment', 'taxes', 'subscriptions', 'income', 'salary',
    'freelance', 'other'
);
CREATE TYPE recurrence_type AS ENUM ('daily', 'weekly', 'biweekly', 'monthly', 'quarterly', 'yearly');
CREATE TYPE goal_status AS ENUM ('active', 'completed', 'paused', 'cancelled');
CREATE TYPE investment_type AS ENUM (
    'stock', 'crypto', 'mutual_fund', 'sip', 'etf',
    'fixed_deposit', 'ppf', 'nps', 'real_estate', 'gold', 'bonds'
);
CREATE TYPE notification_type AS ENUM (
    'budget_alert', 'fraud_alert', 'goal_milestone', 'bill_reminder',
    'ai_insight', 'system', 'marketing'
);

-- ==============================================================================
-- CORE TABLES
-- ==============================================================================

-- Users (managed by auth-service)
CREATE TABLE IF NOT EXISTS users (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                   VARCHAR(255) UNIQUE NOT NULL,
    username                VARCHAR(100) UNIQUE,
    full_name               VARCHAR(255) NOT NULL,
    hashed_password         VARCHAR(255),
    phone_number            VARCHAR(20),
    avatar_url              TEXT,
    role                    user_role NOT NULL DEFAULT 'free',
    status                  user_status NOT NULL DEFAULT 'pending_verification',
    is_verified             BOOLEAN NOT NULL DEFAULT FALSE,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    mfa_enabled             BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret              VARCHAR(64),
    mfa_backup_codes        TEXT[],
    failed_login_attempts   INTEGER DEFAULT 0,
    locked_until            TIMESTAMPTZ,
    last_login_at           TIMESTAMPTZ,
    last_login_ip           VARCHAR(45),
    password_changed_at     TIMESTAMPTZ,
    preferences             JSONB DEFAULT '{}',
    metadata                JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at              TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- OAuth Accounts
CREATE TABLE IF NOT EXISTS oauth_accounts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider            VARCHAR(50) NOT NULL,
    provider_user_id    VARCHAR(255) NOT NULL,
    provider_email      VARCHAR(255),
    access_token        TEXT,
    refresh_token       TEXT,
    token_expires_at    TIMESTAMPTZ,
    provider_data       JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(provider, provider_user_id)
);

-- User Sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash  VARCHAR(255) UNIQUE NOT NULL,
    ip_address          VARCHAR(45),
    user_agent          TEXT,
    device_info         JSONB,
    is_active           BOOLEAN DEFAULT TRUE,
    expires_at          TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auth Audit Logs
CREATE TABLE IF NOT EXISTS auth_audit_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id),
    event       VARCHAR(100) NOT NULL,
    ip_address  VARCHAR(45),
    user_agent  TEXT,
    success     BOOLEAN NOT NULL,
    metadata    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_event ON auth_audit_logs(user_id, event);
CREATE INDEX idx_audit_logs_created ON auth_audit_logs(created_at DESC);

-- ==============================================================================
-- FINANCIAL TABLES (managed by expense-service)
-- ==============================================================================

-- Bank Accounts
CREATE TABLE IF NOT EXISTS accounts (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL,
    name                    VARCHAR(255) NOT NULL,
    account_type            VARCHAR(50) NOT NULL,
    balance                 NUMERIC(15,2) DEFAULT 0,
    currency                VARCHAR(3) DEFAULT 'INR',
    bank_name               VARCHAR(255),
    account_number_last4    VARCHAR(4),
    is_primary              BOOLEAN DEFAULT FALSE,
    is_active               BOOLEAN DEFAULT TRUE,
    plaid_account_id        VARCHAR(255),
    metadata                JSONB,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_accounts_user_id ON accounts(user_id);

-- Expenses
CREATE TABLE IF NOT EXISTS expenses (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL,
    account_id              UUID REFERENCES accounts(id),
    title                   VARCHAR(255) NOT NULL,
    description             TEXT,
    amount                  NUMERIC(15,2) NOT NULL CHECK (amount > 0),
    currency                VARCHAR(3) NOT NULL DEFAULT 'INR',
    category                expense_category NOT NULL,
    sub_category            VARCHAR(100),
    tags                    JSONB DEFAULT '[]',
    transaction_type        transaction_type NOT NULL DEFAULT 'debit',
    merchant_name           VARCHAR(255),
    merchant_category       VARCHAR(100),
    location                VARCHAR(255),
    is_recurring            BOOLEAN DEFAULT FALSE,
    recurrence_type         recurrence_type,
    recurrence_end_date     DATE,
    expense_date            DATE NOT NULL,
    ai_category_confidence  NUMERIC(4,3),
    is_tax_deductible       BOOLEAN DEFAULT FALSE,
    tax_category            VARCHAR(100),
    is_flagged              BOOLEAN DEFAULT FALSE,
    fraud_score             NUMERIC(4,3),
    metadata                JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_expenses_user_date ON expenses(user_id, expense_date DESC);
CREATE INDEX idx_expenses_user_category ON expenses(user_id, category);
CREATE INDEX idx_expenses_amount ON expenses(amount);
CREATE INDEX idx_expenses_fraud ON expenses(is_flagged, fraud_score) WHERE is_flagged = TRUE;

-- Receipts
CREATE TABLE IF NOT EXISTS receipts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_id      UUID REFERENCES expenses(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL,
    file_url        TEXT NOT NULL,
    file_name       VARCHAR(255) NOT NULL,
    file_type       VARCHAR(50) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    ocr_text        TEXT,
    ocr_data        JSONB,
    is_processed    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Budgets
CREATE TABLE IF NOT EXISTS budgets (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL,
    name                    VARCHAR(255) NOT NULL,
    category                expense_category,
    amount                  NUMERIC(15,2) NOT NULL,
    spent_amount            NUMERIC(15,2) DEFAULT 0,
    period                  VARCHAR(20) NOT NULL,
    period_start            DATE NOT NULL,
    period_end              DATE NOT NULL,
    alert_threshold_pct     NUMERIC(5,2) DEFAULT 80.0,
    is_ai_generated         BOOLEAN DEFAULT FALSE,
    is_active               BOOLEAN DEFAULT TRUE,
    notes                   TEXT,
    metadata                JSONB,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_budgets_user ON budgets(user_id, is_active);

-- Subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,
    name                VARCHAR(255) NOT NULL,
    provider            VARCHAR(255) NOT NULL,
    amount              NUMERIC(15,2) NOT NULL,
    currency            VARCHAR(3) DEFAULT 'INR',
    billing_cycle       recurrence_type NOT NULL,
    next_billing_date   DATE NOT NULL,
    category            VARCHAR(100),
    is_active           BOOLEAN DEFAULT TRUE,
    is_used             BOOLEAN DEFAULT TRUE,
    cancellation_url    TEXT,
    notes               TEXT,
    last_detected_at    TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Goals
CREATE TABLE IF NOT EXISTS goals (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL,
    name                    VARCHAR(255) NOT NULL,
    description             TEXT,
    target_amount           NUMERIC(15,2) NOT NULL,
    current_amount          NUMERIC(15,2) DEFAULT 0,
    target_date             DATE,
    category                VARCHAR(100) NOT NULL,
    status                  goal_status DEFAULT 'active',
    monthly_contribution    NUMERIC(15,2),
    is_ai_planned           BOOLEAN DEFAULT FALSE,
    ai_plan                 JSONB,
    priority                INTEGER DEFAULT 1,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Investments
CREATE TABLE IF NOT EXISTS investments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    name            VARCHAR(255) NOT NULL,
    symbol          VARCHAR(50),
    investment_type investment_type NOT NULL,
    quantity        NUMERIC(20,8),
    buy_price       NUMERIC(15,4) NOT NULL,
    current_price   NUMERIC(15,4),
    buy_date        DATE NOT NULL,
    total_invested  NUMERIC(15,2) NOT NULL,
    current_value   NUMERIC(15,2),
    returns_pct     NUMERIC(8,4),
    is_active       BOOLEAN DEFAULT TRUE,
    platform        VARCHAR(100),
    notes           TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- AI TABLES (managed by ai-service)
-- ==============================================================================

-- AI Insights
CREATE TABLE IF NOT EXISTS ai_insights (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    insight_type    VARCHAR(100) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    content         TEXT NOT NULL,
    data            JSONB,
    confidence      NUMERIC(4,3),
    is_read         BOOLEAN DEFAULT FALSE,
    is_dismissed    BOOLEAN DEFAULT FALSE,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_insights_user ON ai_insights(user_id, is_read, created_at DESC);

-- Fraud Alerts
CREATE TABLE IF NOT EXISTS fraud_alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    expense_id      UUID REFERENCES expenses(id),
    fraud_score     NUMERIC(4,3) NOT NULL,
    risk_level      VARCHAR(20) NOT NULL,
    risk_factors    JSONB DEFAULT '[]',
    recommendation  TEXT,
    is_resolved     BOOLEAN DEFAULT FALSE,
    resolved_at     TIMESTAMPTZ,
    resolution_note TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_fraud_alerts_user ON fraud_alerts(user_id, is_resolved);

-- Financial Health Scores
CREATE TABLE IF NOT EXISTS financial_scores (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL,
    overall_score           NUMERIC(5,2) NOT NULL,
    overall_grade           VARCHAR(3) NOT NULL,
    savings_score           NUMERIC(5,2),
    debt_score              NUMERIC(5,2),
    budget_score            NUMERIC(5,2),
    investment_score        NUMERIC(5,2),
    emergency_fund_score    NUMERIC(5,2),
    cash_flow_score         NUMERIC(5,2),
    breakdown               JSONB,
    recommendations         JSONB DEFAULT '[]',
    calculated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_financial_scores_user ON financial_scores(user_id, calculated_at DESC);

-- ==============================================================================
-- NOTIFICATION TABLE
-- ==============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    type            notification_type NOT NULL,
    title           VARCHAR(255) NOT NULL,
    message         TEXT NOT NULL,
    data            JSONB,
    is_read         BOOLEAN DEFAULT FALSE,
    is_sent         BOOLEAN DEFAULT FALSE,
    sent_via        TEXT[],
    scheduled_at    TIMESTAMPTZ,
    sent_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);

-- ==============================================================================
-- TRIGGERS: Auto-update `updated_at`
-- ==============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_accounts_updated_at BEFORE UPDATE ON accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_expenses_updated_at BEFORE UPDATE ON expenses FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_budgets_updated_at BEFORE UPDATE ON budgets FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_goals_updated_at BEFORE UPDATE ON goals FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_investments_updated_at BEFORE UPDATE ON investments FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ==============================================================================
-- INITIAL SEED DATA (Development Only)
-- ==============================================================================

-- Super Admin user (change password immediately!)
INSERT INTO users (id, email, full_name, hashed_password, role, status, is_verified, is_active)
VALUES (
    gen_random_uuid(),
    'admin@expenseflowx.com',
    'Super Admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY2l.dZ.KP1hWsq',  -- "Admin@1234!"
    'super_admin',
    'active',
    TRUE,
    TRUE
) ON CONFLICT DO NOTHING;

-- Done!
SELECT 'ExpenseFlow X database initialized successfully!' AS status;
