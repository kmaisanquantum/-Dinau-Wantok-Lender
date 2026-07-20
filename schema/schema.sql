-- =====================================================================
-- Wantok Lender — Core PostgreSQL Schema
-- Multi-tenant B2B micro-finance ledger for PNG street/MSME lenders
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";      -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "citext";        -- case-insensitive text

-- ---------------------------------------------------------------------
-- updated_at helper trigger function (must exist before any table
-- below attaches a trigger to it)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------
-- ENUM TYPES
-- ---------------------------------------------------------------------
CREATE TYPE loan_status AS ENUM (
    'pending', 'active', 'overdue', 'defaulted', 'closed', 'written_off'
);

CREATE TYPE collateral_status AS ENUM (
    'in_vault', 'returned', 'forfeited', 'sold', 'disputed'
);

CREATE TYPE transaction_type AS ENUM (
    'disbursement', 'repayment', 'fee', 'penalty', 'adjustment'
);

CREATE TYPE sync_conflict_state AS ENUM (
    'none', 'resolved_server_wins', 'resolved_client_wins', 'manual_review'
);

-- ---------------------------------------------------------------------
-- TENANTS  (distinct lending operations/businesses on the platform)
-- ---------------------------------------------------------------------
CREATE TABLE tenants (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_name       TEXT NOT NULL,
    registration_number TEXT,                 -- IPA / business registry ref, nullable for informal lenders
    province            TEXT,
    contact_phone       TEXT,
    contact_email       CITEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    max_interest_rate_bp INTEGER NOT NULL DEFAULT 3000, -- basis points/month cap, tenant-configurable ceiling
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_tenants_updated
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------
-- BORROWERS
-- Identity is stored ONLY as salted SHA-256 hashes so that the
-- cross-tenant fraud-flag lookup never leaks raw PII between tenants.
-- Human-readable details are tenant-scoped and encrypted at rest
-- (encryption performed at the application layer with pgcrypto's
-- symmetric functions keyed per-tenant; ciphertext only in DB).
-- ---------------------------------------------------------------------
CREATE TABLE borrowers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    phone_hash          CHAR(64) NOT NULL,     -- SHA-256(hex) of E.164 phone + pepper
    national_id_hash     CHAR(64),              -- SHA-256(hex) of national ID + pepper, nullable

    -- Tenant-local encrypted metadata (bytea ciphertext, app-layer AES via pgcrypto)
    encrypted_full_name  BYTEA NOT NULL,
    encrypted_address    BYTEA,
    encrypted_employer   BYTEA,                 -- e.g. public service department, for Alesco borrowers

    is_public_servant    BOOLEAN NOT NULL DEFAULT FALSE,
    alesco_file_number   TEXT,                  -- nullable, only for public-service payroll borrowers

    risk_flag            TEXT NOT NULL DEFAULT 'none', -- 'none' | 'watch' | 'high'
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (tenant_id, phone_hash)
);

CREATE INDEX idx_borrowers_phone_hash ON borrowers (phone_hash);
CREATE INDEX idx_borrowers_national_id_hash ON borrowers (national_id_hash) WHERE national_id_hash IS NOT NULL;
CREATE INDEX idx_borrowers_tenant ON borrowers (tenant_id);

CREATE TRIGGER trg_borrowers_updated
    BEFORE UPDATE ON borrowers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------
-- LOANS
-- ---------------------------------------------------------------------
CREATE TABLE loans (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id             UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    borrower_id           UUID NOT NULL REFERENCES borrowers(id) ON DELETE RESTRICT,

    principal_amount      NUMERIC(14,2) NOT NULL CHECK (principal_amount > 0),
    interest_rate_bp      INTEGER NOT NULL CHECK (interest_rate_bp >= 0), -- basis points per compounding period
    compounding_period    TEXT NOT NULL DEFAULT 'fortnightly'
                            CHECK (compounding_period IN ('weekly','fortnightly','monthly')),
    term_periods          INTEGER NOT NULL CHECK (term_periods > 0),

    disbursed_at          TIMESTAMPTZ,
    due_at                TIMESTAMPTZ,

    outstanding_balance   NUMERIC(14,2) NOT NULL DEFAULT 0,
    status                loan_status NOT NULL DEFAULT 'pending',

    -- Alesco 50% net-pay retention ceiling check, snapshotted at disbursement
    net_pay_at_disbursement     NUMERIC(14,2),
    total_deduction_pct_at_disbursement NUMERIC(5,2), -- existing + this loan's deduction, must stay <= 50.00

    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_loans_tenant ON loans (tenant_id);
CREATE INDEX idx_loans_borrower ON loans (borrower_id);
CREATE INDEX idx_loans_status ON loans (status) WHERE status IN ('active','overdue');

CREATE TRIGGER trg_loans_updated
    BEFORE UPDATE ON loans
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------
-- COLLATERAL LOGS  (physical items held against a loan)
-- ---------------------------------------------------------------------
CREATE TABLE collateral_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    loan_id             UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,

    item_description    TEXT NOT NULL,           -- e.g. "Samsung A14, IMEI ends 4471"
    item_category       TEXT NOT NULL DEFAULT 'other'
                            CHECK (item_category IN ('phone','laptop','tool','jewelry','document','other')),
    estimated_value     NUMERIC(12,2),
    storage_location    TEXT NOT NULL,           -- vault/branch code
    custody_status      collateral_status NOT NULL DEFAULT 'in_vault',

    received_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    released_at         TIMESTAMPTZ,
    released_to         TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_collateral_loan ON collateral_logs (loan_id);
CREATE INDEX idx_collateral_status ON collateral_logs (custody_status);

CREATE TRIGGER trg_collateral_updated
    BEFORE UPDATE ON collateral_logs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------
-- TRANSACTIONS  (repayment ledger, append-only)
-- ---------------------------------------------------------------------
CREATE TABLE transactions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    loan_id             UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,

    type                transaction_type NOT NULL,
    amount              NUMERIC(14,2) NOT NULL CHECK (amount > 0),
    balance_after        NUMERIC(14,2) NOT NULL,

    -- Offline-sync provenance
    client_node_id       TEXT,                    -- device/agent identifier that recorded this
    client_generated_id  UUID NOT NULL,            -- UUID generated client-side, idempotency key
    client_recorded_at   TIMESTAMPTZ NOT NULL,     -- device-local timestamp when txn actually happened
    server_received_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload_signature    TEXT NOT NULL,            -- base64 signature, verified before commit
    sync_conflict_state  sync_conflict_state NOT NULL DEFAULT 'none',

    notes                TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (tenant_id, client_generated_id)         -- idempotent replay protection
);

CREATE INDEX idx_transactions_loan ON transactions (loan_id);
CREATE INDEX idx_transactions_tenant_time ON transactions (tenant_id, server_received_at);

-- End of schema. Apply with: psql "$DATABASE_URL" -f schema/schema.sql
