from uuid import uuid4

from app.jobs import run_monthly_usage_rollup
from app.models import (
    Plan,
    PlanName,
    Subscription,
    SubscriptionStatus,
    Tenant,
    UsageEvent,
    UsageType,
)
from tests.conftest import TestingSessionLocal


def test_usage_rollup_is_safe_to_run_twice(monkeypatch):
    """Running the rollup twice must not create duplicate usage."""

    database = TestingSessionLocal()

    free_plan = database.query(Plan).filter(
        Plan.name == PlanName.FREE
    ).one()

    tenant = Tenant(
        name=f"Rollup Tenant {uuid4()}",
    )

    tenant.subscription = Subscription(
        plan=free_plan,
        status=SubscriptionStatus.ACTIVE,
    )

    database.add(tenant)
    database.flush()

    database.add(
        UsageEvent(
            tenant_id=tenant.id,
            usage_type=UsageType.AI_TOKENS,
            quantity=100,
            idempotency_key=f"rollup-{uuid4()}",
            request_hash="a" * 64,
            input_tokens=100,
            cached_input_tokens=0,
            output_tokens=0,
            reasoning_tokens=0,
            cost_microcents=25_000,
        )
    )

    database.commit()
    tenant_id = tenant.id
    database.close()

    monkeypatch.setattr(
        "app.jobs.SessionLocal",
        TestingSessionLocal,
    )

    first_rollup = run_monthly_usage_rollup()
    second_rollup = run_monthly_usage_rollup()

    first_tenant_summary = next(
        item
        for item in first_rollup
        if item["tenant_id"] == tenant_id
    )

    second_tenant_summary = next(
        item
        for item in second_rollup
        if item["tenant_id"] == tenant_id
    )

    assert first_tenant_summary == second_tenant_summary
    assert first_tenant_summary["api_calls"] == 1
    assert first_tenant_summary["ai_tokens"] == 100
    assert first_tenant_summary["cost_microcents"] == 25_000