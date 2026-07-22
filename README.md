# Wantok Lender

Multi-tenant B2B micro-finance platform for PNG street lenders and
registered MSME finance operators — offline-tolerant, self-hostable,
built for volatile connectivity and grid instability.

## Repo layout

```
schema/               PostgreSQL multi-tenant schema (schema.sql)
backend/               FastAPI service (Python 3.12)
  app/core/            config, DB session, crypto helpers, auth deps
  app/models/          SQLAlchemy ORM models + Pydantic schemas
  app/routers/         credit-check, sync, payslip HTTP endpoints
  app/services/        credit_checker, sync_pipeline, payslip_parser
frontend/              React + Tailwind merchant/lender dashboard
docs/                  Design docs (payslip parsing pipeline, etc.)
docker-compose.yml     Coolify-ready multi-service deploy
```

## What's implemented

- **Schema**: `tenants` (with password-based authentication), `borrowers` (SHA-256-hashed identity, AES-GCM
  encrypted PII), `loans` (with Alesco ceiling snapshot fields),
  `collateral_logs`, `transactions` (idempotent, signed).
- **Authentication system**: Secure JWT-based multi-tenant authentication (`POST /api/v1/auth/login` and `GET /api/v1/auth/me`).
- **Anonymized cross-tenant credit checker**: hashes a phone/ID and
  returns only an aggregate risk tier + counts — never another
  tenant's identity or loan details.
- **Offline sync pipeline**: ingests signed batches from SQLite edge
  nodes, verifies HMAC signatures, applies atomically, and is
  idempotent on `(tenant_id, client_generated_id)` so retried uploads
  over flaky data never double-post a repayment.
- **Alesco payslip parser**: OCR + regex extraction of Gross/Net Pay
  and deduction lines, with a reconciliation check and a 50%-ceiling
  compliance check. See `docs/payslip_parsing.md`.
- **Tenant CRUD management APIs**: Fully implemented and secure routes for creating and listing borrowers, issuing loans (with compliance checks), logging/releasing physical collateral, and recording repayments.
- **Lender dashboard**: Live statistics including Total Capital Out, Expected Fortnightly Repayments, At-Risk Accounts, and Collateral Vault.

## Seeding & Demo Access

The system comes with an idempotent automatic database seeder. On startup, a demo tenant with live statistics, multiple registered borrowers, outstanding loans, and collateral logs is created.

- **Seed login email**: `seed@wantok.com`
- **Password**: `password123`

## What you still need to add before production

- Device-secret provisioning/rotation for the sync pipeline's HMAC
  signing (currently passed in as a header per request).
- Real Alembic migrations instead of the single `schema.sql`, once the
  schema needs to evolve post-launch.

## Local development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real secrets
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Deploying on a self-hosted VPS via Coolify

1. Push this repo to GitHub (see below).
2. In Coolify: **New Resource → Docker Compose**, point it at this
   repo, `docker-compose.yml` at the root.
3. Set environment variables in Coolify's UI (never commit them):
   `POSTGRES_PASSWORD`, `HASH_PEPPER`, `FIELD_ENCRYPTION_KEY`,
   `JWT_SECRET`, `PUBLIC_API_URL`.
   Generate `FIELD_ENCRYPTION_KEY` with:
   ```bash
   python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"
   ```
4. Deploy. Coolify builds `backend/Dockerfile` and
   `frontend/Dockerfile`, and initializes Postgres from
   `schema/schema.sql` on first boot via the compose file's
   `docker-entrypoint-initdb.d` mount.
5. Point your domain at Coolify's reverse proxy and enable Let's
   Encrypt in the Coolify UI for TLS.

## Pushing to GitHub

```bash
cd wantok-lender
git init
git add .
git commit -m "Initial scaffold: schema, backend, dashboard"
git branch -M main
git remote add origin https://github.com/<your-org>/wantok-lender.git
git push -u origin main
```
