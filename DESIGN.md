# Design Document — Usage Metering & Billing Engine

## 1. Problem

SaaS applications need to know:

1. How much each customer has used.
2. Whether the customer has reached their plan limit.
3. How much the usage costs.
4. Whether the customer has an active subscription.

This backend will record usage safely, enforce monthly quotas, calculate costs using integer money values, and synchronize subscription status using verified Stripe test-mode webhooks.

## 2. Technology Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic database migrations
- Stripe test mode
- Pytest
- Docker Compose

## 3. Plans and Monthly Quotas

| Plan | API Calls | AI Tokens |
|---|---:|---:|
| Free | 1,000 | 100,000 |
| Pro | 10,000 | 1,000,000 |

The Free plan is assigned when a tenant is created.

The Pro plan is assigned only after a valid Stripe webhook confirms the subscription.

## 4. Database Schema

### tenants

Stores customer organizations.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| name | String | Tenant name |
| created_at | DateTime | Creation time |

### plans

Stores available plans and their quotas.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| name | String | Free or Pro |
| api_call_limit | Integer | Monthly API-call quota |
| ai_token_limit | Integer | Monthly AI-token quota |

### subscriptions

Stores the subscription state of each tenant.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| tenant_id | UUID | Tenant owner |
| plan_id | UUID | Current plan |
| stripe_customer_id | String | Stripe customer identifier |
| stripe_subscription_id | String | Stripe subscription identifier |
| status | String | active, canceled, or unpaid |
| current_period_start | DateTime | Billing period start |
| current_period_end | DateTime | Billing period end |

### usage_events

Stores every billable action.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| tenant_id | UUID | Tenant that created the usage |
| usage_type | String | api_call or ai_tokens |
| quantity | Integer | Amount used |
| idempotency_key | String | Prevents duplicate recording |
| input_tokens | Integer | Fresh input tokens |
| cached_input_tokens | Integer | Discounted cached tokens |
| output_tokens | Integer | Output tokens |
| reasoning_tokens | Integer | Tokens priced as output |
| cost_microcents | Integer | Calculated cost without floats |
| created_at | DateTime | Event creation time |

The combination of `tenant_id` and `idempotency_key` will have a unique database constraint.

### stripe_events

Stores processed Stripe webhook IDs.

| Column | Type | Description |
|---|---|---|
| id | String | Stripe event ID and primary key |
| event_type | String | Stripe webhook type |
| processed_at | DateTime | Processing time |

This table prevents the same Stripe webhook from being processed twice.

## 5. API Endpoints

### `POST /tenants`

Creates a tenant on the Free plan.

### `POST /generate`

Represents one dummy billable AI action.

Required header:

```text
Idempotency-Key: unique-request-key