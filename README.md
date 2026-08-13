# Usage Metering & Billing Engine

A production-style FastAPI backend that records tenant usage, prevents duplicate billing, enforces monthly quotas, calculates token costs, and synchronizes subscription plans using Stripe Sandbox.

## Project Status

Complete implementation with automated tests, PostgreSQL, Alembic migrations, Stripe Checkout, verified webhooks, and a retry-safe background rollup job.

## Core Features

- Multi-tenant Free and Pro subscriptions
- Idempotent usage recording
- Duplicate-request conflict detection
- Monthly API-call and AI-token quotas
- HTTP `402`, `409`, and `429` billing safeguards
- Integer-only token cost calculations
- Stripe Sandbox Checkout sessions
- Signature-verified Stripe webhooks
- Duplicate webhook prevention
- PostgreSQL database with Alembic migrations
- Retry-safe monthly usage rollup job
- Automated tests for critical billing behaviour

## Technology Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Stripe Sandbox
- Pydantic Settings
- Pytest
- Docker Compose

## Subscription Plans

| Plan | Monthly API Calls | Monthly AI Tokens |
| --- | ---: | ---: |
| Free | 1,000 | 100,000 |
| Pro | 10,000 | 1,000,000 |

## Architecture

```text
Client
  |
  v
FastAPI endpoints
  |
  +-- Tenant service
  +-- Metering and quota service
  +-- Integer pricing service
  +-- Stripe Checkout and webhook service
  |
  v
SQLAlchemy
  |
  v
PostgreSQL
```

Stripe sends signed events to `POST /webhooks/stripe`. The application verifies the signature, ignores duplicate events, and synchronizes the local subscription.

## Database Tables

- `tenants` - customer organizations
- `plans` - Free and Pro limits
- `subscriptions` - tenant plan and Stripe status
- `usage_events` - idempotent billable usage records
- `stripe_events` - processed Stripe event IDs

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Check application health |
| POST | `/tenants` | Create a tenant with a Free subscription |
| POST | `/generate` | Record simulated AI-token usage |
| GET | `/usage/{tenant_id}` | View monthly usage, limits, and cost |
| POST | `/checkout/{tenant_id}` | Create a Stripe Pro Checkout session |
| POST | `/webhooks/stripe` | Receive verified Stripe events |

The `/generate` endpoint requires an `Idempotency-Key` header.

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/nangialayhamidi796-bot/flyrank-capstone-metering-billing.git
cd flyrank-capstone-metering-billing
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Create the environment file

```powershell
Copy-Item .env.example .env
```

Add your own Stripe Sandbox values to `.env`. Never commit `.env` or real secrets.

### 5. Start PostgreSQL

Make sure Docker Desktop is running, then execute:

```powershell
docker compose up -d
docker compose ps
```

### 6. Apply database migrations

```powershell
alembic upgrade head
```

### 7. Seed the plans

```powershell
python -m app.seed
```

### 8. Start the API

```powershell
uvicorn app.main:app --reload
```

Open the interactive documentation:

```text
http://127.0.0.1:8000/docs
```

## Stripe Webhook Testing

Install and authenticate the Stripe CLI, then forward Sandbox events:

```powershell
stripe login
stripe listen --forward-to http://127.0.0.1:8000/webhooks/stripe
```

Copy the generated `whsec_...` value into `STRIPE_WEBHOOK_SECRET` in `.env`, then restart the API.

All Stripe operations in this project use Sandbox mode. No real money is charged.

## Run Automated Tests

```powershell
pytest -q
```

Expected result:

```text
16 passed
```

The current Starlette `TestClient` deprecation warning comes from a dependency and does not cause a test failure.

## Run the Background Job

```powershell
python -m app.jobs
```

The job performs a retry-safe monthly usage rollup.

## Idempotency Behaviour

Every billable request includes a tenant-specific idempotency key.

- Same key and same request: returns the original event without double counting.
- Same key and different request: returns HTTP `409 Conflict`.
- New request over quota: returns HTTP `429 Too Many Requests`.
- Inactive or unpaid subscription: returns HTTP `402 Payment Required`.

## Additional Documentation

- [DESIGN.md](DESIGN.md) - architecture, schema, API contract, and design decisions
- [BUILDLOG.md](BUILDLOG.md) - implementation progress and engineering decisions
- [EVIDENCE.md](EVIDENCE.md) - verification evidence and important test results
- [capstone.yaml](capstone.yaml) - machine-readable project commands

## Limitations

- Stripe Sandbox only
- AI generation is simulated
- No real payment processing
- No frontend application
- No proration or overage invoicing
- Local Docker deployment only

## Security

- Real secrets are stored only in the ignored `.env` file.
- `.env.example` contains placeholder values.
- Stripe webhook signatures are verified before processing.
- Stripe event IDs prevent duplicate webhook processing.
- Money calculations use integers to avoid floating-point errors.