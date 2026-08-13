from datetime import datetime, timezone

import stripe
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    Plan,
    PlanName,
    StripeEvent,
    Subscription,
    SubscriptionStatus,
    Tenant,
)


def create_checkout_session(
    database: Session,
    tenant_id: str,
) -> dict:
    """Create a Stripe test-mode subscription Checkout session."""

    tenant = database.scalar(
        select(Tenant).where(Tenant.id == tenant_id)
    )

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )

    if not settings.stripe_secret_key.startswith("sk_test_"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe test secret key is not configured.",
        )

    if not settings.stripe_pro_price_id.startswith("price_"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe Pro price ID is not configured.",
        )

    stripe.api_key = settings.stripe_secret_key

    try:
        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[
                {
                    "price": settings.stripe_pro_price_id,
                    "quantity": 1,
                }
            ],
            success_url=(
                "http://127.0.0.1:8000/docs"
                "?checkout=success&session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=(
                "http://127.0.0.1:8000/docs"
                "?checkout=canceled"
            ),
            client_reference_id=tenant.id,
            metadata={
                "tenant_id": tenant.id,
            },
            subscription_data={
                "metadata": {
                    "tenant_id": tenant.id,
                }
            },
        )

    except stripe.StripeError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe could not create the Checkout session.",
        ) from error

    return {
        "checkout_url": checkout_session.url,
        "session_id": checkout_session.id,
    }


def stripe_datetime(
    timestamp: int | None,
) -> datetime | None:
    """Convert a Stripe Unix timestamp to UTC."""

    if timestamp is None:
        return None

    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc,
    )


def local_subscription_status(
    stripe_status: str | None,
) -> SubscriptionStatus:
    """Convert a Stripe status into a local status."""

    if stripe_status in {"active", "trialing"}:
        return SubscriptionStatus.ACTIVE

    if stripe_status in {
        "unpaid",
        "past_due",
        "incomplete",
    }:
        return SubscriptionStatus.UNPAID

    return SubscriptionStatus.CANCELED

def stripe_object_to_dict(value):
    """Recursively convert Stripe objects into Python values."""

    if hasattr(value, "_data"):
        value = value._data

    if isinstance(value, dict):
        return {
            key: stripe_object_to_dict(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            stripe_object_to_dict(item)
            for item in value
        ]

    return value


def process_stripe_webhook(
    database: Session,
    payload: bytes,
    signature: str,
) -> dict:
    """Verify and process one Stripe event exactly once."""

    if not settings.stripe_webhook_secret.startswith("whsec_"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook secret is not configured.",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.stripe_webhook_secret,
        )

    except (
        ValueError,
        stripe.SignatureVerificationError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe webhook signature.",
        ) from error

    event_id = event["id"]
    event_type = event["type"]

    existing_event = database.get(
        StripeEvent,
        event_id,
    )

    if existing_event is not None:
        return {
            "received": True,
            "duplicate": True,
            "event_id": event_id,
        }

    stripe_object = event["data"]["object"]

    # Stripe returns a custom StripeObject.
    # Convert it to a normal dictionary for safe .get() calls.
    if hasattr(stripe_object, "to_dict_recursive"):
        stripe_object = stripe_object.to_dict_recursive()

    if event_type == "checkout.session.completed":
        handle_checkout_completed(
            database=database,
            stripe_object=stripe_object,
        )

    elif event_type in {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }:
        handle_subscription_event(
            database=database,
            event_type=event_type,
            stripe_object=stripe_object,
        )

    database.add(
        StripeEvent(
            id=event_id,
            event_type=event_type,
        )
    )
    database.commit()

    return {
        "received": True,
        "duplicate": False,
        "event_id": event_id,
    }
def stripe_value(
    stripe_object,
    key: str,
    default=None,
):
    """Read a value from either a dictionary or StripeObject."""

    try:
        return stripe_object[key]
    except (KeyError, TypeError):
        return default

def handle_checkout_completed(
    database: Session,
    stripe_object,
) -> None:
    """Upgrade a tenant after completed Checkout."""

    metadata = stripe_value(
        stripe_object,
        "metadata",
        {},
    )

    tenant_id = (
        stripe_value(
            stripe_object,
            "client_reference_id",
        )
        or stripe_value(
            metadata,
            "tenant_id",
        )
    )

    tenant = database.get(Tenant, tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook tenant not found.",
        )

    pro_plan = database.scalar(
        select(Plan).where(Plan.name == PlanName.PRO)
    )

    if pro_plan is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pro plan is missing. Run the seed command first.",
        )

    tenant.subscription.plan = pro_plan
    tenant.subscription.status = SubscriptionStatus.ACTIVE
    tenant.subscription.stripe_customer_id = stripe_value(
        stripe_object,
        "customer",
    )
    tenant.subscription.stripe_subscription_id = stripe_value(
        stripe_object,
        "subscription",
    )


def handle_subscription_event(
    database: Session,
    event_type: str,
    stripe_object: dict,
) -> None:
    """Synchronize a Stripe subscription with a tenant."""

    stripe_subscription_id = stripe_object.get("id")
    tenant_id = stripe_object.get(
        "metadata",
        {},
    ).get("tenant_id")

    subscription = database.scalar(
        select(Subscription).where(
            Subscription.stripe_subscription_id
            == stripe_subscription_id
        )
    )

    if subscription is None and tenant_id:
        tenant = database.get(Tenant, tenant_id)

        if tenant is not None:
            subscription = tenant.subscription

    if subscription is None:
        return

    subscription.stripe_subscription_id = stripe_subscription_id
    subscription.stripe_customer_id = stripe_object.get("customer")
    subscription.current_period_start = stripe_datetime(
        stripe_object.get("current_period_start")
    )
    subscription.current_period_end = stripe_datetime(
        stripe_object.get("current_period_end")
    )

    if event_type == "customer.subscription.deleted":
        free_plan = database.scalar(
            select(Plan).where(Plan.name == PlanName.FREE)
        )

        if free_plan is not None:
            subscription.plan = free_plan

        subscription.status = SubscriptionStatus.CANCELED
        return

    pro_plan = database.scalar(
        select(Plan).where(Plan.name == PlanName.PRO)
    )

    if pro_plan is not None:
        subscription.plan = pro_plan

    subscription.status = local_subscription_status(
        stripe_object.get("status")
    )