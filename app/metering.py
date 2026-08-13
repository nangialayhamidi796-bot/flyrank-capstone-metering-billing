import hashlib
import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    SubscriptionStatus,
    Tenant,
    UsageEvent,
    UsageType,
)


def current_month_start() -> datetime:
    """Return the first moment of the current month in UTC."""

    now = datetime.now(timezone.utc)

    return datetime(
        year=now.year,
        month=now.month,
        day=1,
        tzinfo=timezone.utc,
    )


def create_request_hash(
    tenant_id: str,
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int,
) -> str:
    """Create a stable fingerprint of one billable request."""

    request_data = {
        "tenant_id": tenant_id,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
    }

    encoded_data = json.dumps(
        request_data,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded_data).hexdigest()

def get_monthly_usage(
    database: Session,
    tenant_id: str,
) -> tuple[int, int, int]:
    """Return API calls, AI tokens, and cost for the current month."""

    month_start = current_month_start()

    result = database.execute(
        select(
            func.count(UsageEvent.id),
            func.coalesce(func.sum(UsageEvent.quantity), 0),
            func.coalesce(func.sum(UsageEvent.cost_microcents), 0),
        ).where(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.created_at >= month_start,
        )
    ).one()

    api_calls_used = int(result[0])
    ai_tokens_used = int(result[1])
    cost_microcents = int(result[2])

    return api_calls_used, ai_tokens_used, cost_microcents

def record_generate_usage(
    database: Session,
    tenant_id: str,
    idempotency_key: str,
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int,
) -> dict:
    """Validate and record one idempotent billable AI action."""

    tenant = database.scalar(
        select(Tenant).where(Tenant.id == tenant_id)
    )

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )

    subscription = tenant.subscription

    if subscription.status != SubscriptionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="The subscription is not active. Upgrade or update payment.",
        )

    request_hash = create_request_hash(
        tenant_id=tenant_id,
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
    )

    existing_event = database.scalar(
        select(UsageEvent).where(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.idempotency_key == idempotency_key,
        )
    )

    if existing_event is not None:
        if existing_event.request_hash != request_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This idempotency key was already used "
                    "with different request data."
                ),
            )

        api_calls_used, ai_tokens_used, total_cost = get_monthly_usage(
            database=database,
            tenant_id=tenant_id,
        )

        return {
            "event_id": existing_event.id,
            "tenant_id": tenant_id,
            "idempotency_key": idempotency_key,
            "api_calls_used": api_calls_used,
            "api_calls_limit": subscription.plan.api_call_limit,
            "ai_tokens_used": ai_tokens_used,
            "ai_tokens_limit": subscription.plan.ai_token_limit,
            "cost_microcents": total_cost,
            "duplicate": True,
        }

    requested_tokens = (
        input_tokens
        + cached_input_tokens
        + output_tokens
        + reasoning_tokens
    )

    api_calls_used, ai_tokens_used, total_cost = get_monthly_usage(
        database=database,
        tenant_id=tenant_id,
    )

    if api_calls_used + 1 > subscription.plan.api_call_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly API-call quota exceeded.",
            headers={"Retry-After": "3600"},
        )

    if ai_tokens_used + requested_tokens > subscription.plan.ai_token_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly AI-token quota exceeded.",
            headers={"Retry-After": "3600"},
        )

    usage_event = UsageEvent(
        tenant_id=tenant_id,
        usage_type=UsageType.AI_TOKENS,
        quantity=requested_tokens,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
        cost_microcents=0,
    )

    database.add(usage_event)
    database.commit()
    database.refresh(usage_event)

    return {
        "event_id": usage_event.id,
        "tenant_id": tenant_id,
        "idempotency_key": idempotency_key,
        "api_calls_used": api_calls_used + 1,
        "api_calls_limit": subscription.plan.api_call_limit,
        "ai_tokens_used": ai_tokens_used + requested_tokens,
        "ai_tokens_limit": subscription.plan.ai_token_limit,
        "cost_microcents": total_cost,
        "duplicate": False,
    }