# Usage Metering & Billing Engine

A backend service that records tenant usage, enforces monthly quotas, calculates usage costs, and synchronizes subscription plans using Stripe test mode.

## Current Status

Phase 1 — Design and project setup.

## Core Features

- Idempotent usage metering
- Monthly quota enforcement
- Integer-based cost calculations
- Stripe test-mode Checkout
- Signature-verified Stripe webhooks
- Duplicate webhook prevention
- Multi-tenant data isolation
- Automated tests for critical billing cases

## Technology Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Stripe test mode
- Pytest
- Docker Compose

## Plans

| Plan | Monthly API Calls | Monthly AI Tokens |
|---|---:|---:|
| Free | 1,000 | 100,000 |
| Pro | 10,000 | 1,000,000 |

## Documentation

See [DESIGN.md](DESIGN.md) for the database schema, API contract, idempotency strategy, architecture, and project scope.

## Setup

Setup instructions will be added as the application is implemented.

## Testing

Testing instructions will be added during the core billing phase.

## Limitations

- Stripe test mode only
- No real payments
- No invoices, proration, or overage billing
- AI token usage is simulated