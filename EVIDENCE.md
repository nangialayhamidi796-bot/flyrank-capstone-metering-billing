# Capstone Evidence

This file will contain real proof for every Definition-of-Done requirement.

## 1. Metering

- [ ] A billable action creates exactly one usage event.
- [ ] Retrying with the same idempotency key does not double-count usage.
- [ ] Automated duplicate-prevention test passes.

Evidence will be added during Phase 2.

## 2. Quotas

- [ ] Usage is checked against the tenant’s plan.
- [ ] A request exactly reaching the limit follows the documented rule.
- [ ] A request exceeding the limit returns HTTP 429.
- [ ] An inactive or unpaid subscription returns HTTP 402.
- [ ] Responses include a clear explanation.

Evidence will be added during Phase 2.

## 3. Cost Calculation

- [ ] Monthly usage rolls up into a cost per tenant.
- [ ] Cached input tokens use the discounted price.
- [ ] Reasoning tokens use the output-token price.
- [ ] Pricing constants are pinned in configuration.
- [ ] Cost-calculation tests pass.

Evidence will be added during Phase 4.

## 4. Stripe Integration

- [ ] Stripe test Checkout works.
- [ ] A verified webhook changes a tenant from Free to Pro.
- [ ] A forged webhook returns HTTP 400.
- [ ] A duplicate Stripe event is processed only once.
- [ ] Subscription updates and deletions update the local plan and status.

Evidence will be added during Phase 3.

## 5. Data Model and Tenant Isolation

- [ ] Database contains tenants, plans, subscriptions, usage events, and Stripe events.
- [ ] Database schema is managed using migrations.
- [ ] Every customer-owned record is associated with a tenant.
- [ ] Tests prove tenant data is isolated.

Evidence will be added during Phases 2 and 4.

## 6. Background Job

- [ ] Usage-rollup job runs outside the request path.
- [ ] The job is safe to retry.
- [ ] Failures are logged.

Evidence will be added during Phase 4.

## 7. Tests and Documentation

- [ ] All automated tests pass.
- [ ] README contains exact setup, run, seed, and test instructions.
- [ ] Architecture diagram is included.
- [ ] `capstone.yaml` contains working commands.
- [ ] `.env.example` contains only safe placeholders.
- [ ] `BUILDLOG.md` honestly records AI assistance and corrections.

Evidence will be added throughout the project.