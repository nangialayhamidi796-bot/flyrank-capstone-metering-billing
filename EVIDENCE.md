# Capstone Evidence

This file records real verification results for the Usage Metering and Billing Engine.

## 1. Idempotent Metering

Status: Complete

- `POST /generate` requires an `Idempotency-Key`.
- A new request creates one usage event.
- Repeating the same key and request does not double-count usage.
- Reusing the key with different data returns HTTP `409`.
- Verified by `tests/test_metering.py`.

## 2. Quota Enforcement

Status: Complete

- Usage below the monthly limit is accepted.
- Usage exactly reaching the limit is accepted.
- Usage exceeding the limit returns HTTP `429`.
- Quota responses include `Retry-After: 3600`.
- Inactive or unpaid subscriptions return HTTP `402`.
- Verified by `tests/test_metering.py`.

## 3. Integer Pricing

Status: Complete

- Pricing uses integer microcents instead of floating-point money.
- Cached input tokens use a discounted rate.
- Reasoning tokens use the output-token rate.
- Monthly usage summaries include accumulated cost.
- Verified by `tests/test_pricing.py` and `tests/test_metering.py`.

## 4. Stripe Sandbox

Status: Complete

- `POST /checkout/{tenant_id}` returned HTTP `200`.
- Stripe returned a Sandbox Checkout URL and test session ID.
- The Sandbox payment flow completed without real money.
- Webhook signatures are verified.
- Invalid signatures return HTTP `400`.
- Completed Checkout upgrades a tenant from Free to Pro.
- Duplicate Stripe event IDs are processed only once.
- Verified by `tests/test_webhooks.py`.

## 5. PostgreSQL and Migrations

Status: Complete

Docker verification:

```text
metering-billing-postgres
Up (healthy)
0.0.0.0:5432->5432/tcp
```

## 6. Background Job

Status: Complete

Command:

```powershell
python -m app.jobs

## 7. Automated Tests

Status: Complete

Final command:

```powershell

## 8. Documentation and Security

Status: Complete

- `README.md` contains complete setup and usage instructions.
- `DESIGN.md` documents the architecture.
- `BUILDLOG.md` records development progress.
- `capstone.yaml` contains project commands.
- `.env.example` contains placeholders only.
- `.env` and database files are ignored by Git.
- Real secrets are not committed.

## Final Checklist

- [x] Idempotent metering
- [x] Monthly quotas
- [x] Integer pricing
- [x] Stripe Sandbox Checkout
- [x] Verified and deduplicated webhooks
- [x] PostgreSQL and Alembic migrations
- [x] Retry-safe background job
- [x] Sixteen passing tests
- [x] Complete documentation
