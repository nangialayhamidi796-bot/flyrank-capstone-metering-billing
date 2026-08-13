# Build Log

This file records how AI assisted the project, what I verified, and what I changed or understood myself.

## Phase 1 — Design and Project Setup

### AI assistance

AI helped me:

- Read and break down the capstone requirements.
- Choose Python, FastAPI, PostgreSQL, and Stripe test mode.
- Plan the database schema and API endpoints.
- Define the idempotency strategy.
- Create the initial project structure and documentation.

### What I verified and learned

I reviewed the proposed design and learned that:

- An idempotency key prevents a retried request from creating duplicate usage.
- The database must uniquely enforce `tenant_id + idempotency_key`.
- A request that reaches the quota exactly is allowed.
- A request that would exceed the quota returns HTTP 429.
- HTTP 402 is used when payment or an upgrade is required.
- Money should be stored as integers, not floating-point values.
- Stripe webhook signatures must be verified before changing subscription data.
- Processed Stripe event IDs must be stored to prevent duplicate webhook handling.
- Real secrets belong in `.env`, which Git ignores.
- `.env.example` contains only safe placeholders.

### Corrections and decisions

- The initial `.gitignore` command was accidentally saved as text inside the file.
- I corrected the file so it contains only the intended ignore patterns.
- I selected a deliberately small core scope: two plans, two usage types, and one dummy billable endpoint.

### Current result

- Public GitHub repository created.
- Python virtual environment created.
- Required dependencies installed.
- Phase 1 design document created.
- Initial README and evaluator manifest created.
- Safe environment-variable template created.