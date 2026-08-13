# Build Log

This file records how AI assisted the project, what I verified, and what I changed or understood myself.

## Phase 1 - Design and Project Setup

### AI assistance

AI helped me:

- Read and break down the capstone requirements.
- Choose Python, FastAPI, PostgreSQL, and Stripe Sandbox.
- Plan the database schema and API endpoints.
- Define the idempotency strategy.
- Create the initial project structure and documentation.

### What I verified and learned

I reviewed the proposed design and learned that:

- An idempotency key prevents retries from creating duplicate usage.
- The database must uniquely enforce `tenant_id + idempotency_key`.
- A request that reaches the quota exactly is allowed.
- A request that exceeds the quota returns HTTP 429.
- HTTP 402 is used when payment or an upgrade is required.
- Money should be stored as integers, not floating-point values.
- Stripe webhook signatures must be verified.
- Stripe event IDs must be stored to prevent duplicate processing.
- Real secrets belong in `.env`, which Git ignores.
- `.env.example` contains safe placeholders only.

### Corrections and decisions

- The initial `.gitignore` command was accidentally saved as file content.
- I corrected `.gitignore` to contain only the intended patterns.
- I selected a small scope with Free and Pro plans and one simulated billable action.

### Result

- Public GitHub repository created.
- Virtual environment created.
- Dependencies installed.
- Design document created.
- Initial project structure created.
- Safe environment template created.

## Phase 2 - Core Metering and Quotas

### AI assistance

AI helped me:

- Create SQLAlchemy database models.
- Create Pydantic request and response schemas.
- Build tenant, generate, and usage endpoints.
- Design idempotency and quota tests.
- Diagnose Python indentation and import errors.

### What I verified and learned

I verified that:

- A tenant receives an active Free subscription.
- Free and Pro plans have different quotas.
- Duplicate requests do not double-count usage.
- A reused key with different data returns HTTP 409.
- Exactly reaching a quota is accepted.
- Exceeding a quota returns HTTP 429.
- An unpaid subscription returns HTTP 402.
- Usage summaries contain monthly totals and limits.

### Corrections and decisions

- I fixed an indentation error in `tests/test_metering.py`.
- I removed duplicate imports and corrected endpoint ordering.
- I added `*.db` to `.gitignore`.
- I used both request hashes and database constraints for idempotency.
- I ran tests before every major commit.

### Result

- Tenant creation works.
- Idempotent metering works.
- Monthly quotas are enforced.
- Usage summaries work.
- Critical metering tests pass.

## Phase 3 - Stripe Sandbox Integration

### AI assistance

AI helped me:

- Create Stripe Sandbox Checkout sessions.
- Add tenant metadata to Checkout and subscriptions.
- Create a verified webhook endpoint.
- Map Stripe events to local subscription state.
- Design invalid-signature and duplicate-event tests.

### What I verified and learned

I verified that:

- Checkout returns a Stripe Sandbox URL.
- Test payments do not use real money.
- The Stripe CLI forwards events to the local API.
- Webhook signatures are checked before processing.
- Completed Checkout upgrades a tenant to Pro.
- Forged signatures return HTTP 400.
- Replayed events are recognized as duplicates.

### Corrections and decisions

- I rotated Stripe test credentials after they were accidentally exposed.
- I kept real credentials only in the ignored `.env` file.
- I corrected the webhook secret to include the `whsec_` prefix.
- I updated the handler to support Stripe SDK objects that do not implement `.get()`.
- I added integration tests after discovering the SDK object difference.
- I handled created, updated, and deleted subscription events.

### Result

- Stripe Sandbox Checkout works.
- Verified webhooks work.
- Duplicate webhook protection works.
- Free-to-Pro synchronization is tested.
- The full suite reached 16 passing tests.

## Phase 4 - Pricing, Jobs, PostgreSQL, and Migrations

### AI assistance

AI helped me:

- Implement integer token pricing.
- Add discounted cached-token pricing.
- Price reasoning tokens using the output-token rate.
- Build a retry-safe monthly rollup job.
- Configure PostgreSQL with Docker Compose.
- Configure Alembic and generate the initial migration.

### What I verified and learned

I verified that:

- Cost calculations use integer microcents.
- Pricing tests use pinned expected results.
- The rollup job runs outside HTTP requests.
- The job completes safely when zero tenants exist.
- Docker reports PostgreSQL as healthy.
- SQLAlchemy connects using the PostgreSQL driver.
- Alembic creates all required tables in an empty database.
- All 16 automated tests pass.

### Corrections and decisions

- I moved `test_pricing.py` from `app` into `tests`.
- I corrected an accidental nested `tests/tests` directory.
- I started Docker Desktop after the Docker daemon connection failed.
- I generated the migration using a separate empty database.
- I removed the temporary `DATABASE_URL` environment override afterward.
- I documented the dependency deprecation warning instead of treating it as a test failure.

### Result

- Integer pricing is complete.
- Retry-safe rollup job is complete.
- PostgreSQL runs in Docker.
- Alembic migrations are verified.
- Final test result is `16 passed`.

## Final Verification

Commands used:

```powershell
docker compose up -d
docker compose ps
alembic upgrade head
python -m app.seed
python -m app.jobs
pytest -q
git status

## AI Usage Statement

AI was used as a development assistant for planning, code examples, debugging, tests, and documentation. I executed the commands myself, reviewed the results, corrected errors, and verified the completed behaviour through automated tests and manual Stripe Sandbox checks.