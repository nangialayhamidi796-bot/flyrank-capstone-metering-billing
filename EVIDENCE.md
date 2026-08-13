# Capstone Evidence

This document records the commands, automated tests, and manual checks used to verify the Usage Metering and Billing Engine.

## 1. Idempotent Metering

Status: Complete

Implementation:

- `app/metering.py` creates billable usage events.
- Each request requires an `Idempotency-Key` header.
- The database has a unique constraint for tenant ID and idempotency key.
- A request hash detects reuse of the same key with different data.

Automated evidence:

- A new request creates one usage event.
- Repeating the same request returns `"duplicate": true`.
- Duplicate requests do not increase usage.
- Reusing a key with different request data returns HTTP `409`.

Test location:

```text
tests/test_metering.py