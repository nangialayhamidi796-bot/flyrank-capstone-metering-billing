from fastapi import (
    Depends,
    FastAPI,
    Header,
    Request,
    status,
)
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db
from app.metering import (
    get_usage_summary,
    record_generate_usage,
)
from app.schemas import (
    CheckoutResponse,
    GenerateRequest,
    GenerateResponse,
    TenantCreate,
    TenantResponse,
    UsageSummaryResponse,
)
from app.services import create_tenant
from app.stripe_service import (
    create_checkout_session,
    process_stripe_webhook,
)


# Create database tables that do not exist yet.
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Usage Metering and Billing Engine",
    description=(
        "API for usage tracking, quota enforcement, "
        "and subscription billing."
    ),
    version="1.0.0",
)


@app.get("/health")
def health_check():
    """Confirm that the backend application is running."""

    return {
        "status": "healthy",
        "service": "usage-metering-billing-engine",
    }


@app.post(
    "/tenants",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_endpoint(
    tenant_data: TenantCreate,
    database: Session = Depends(get_db),
):
    """Create a tenant with an active Free subscription."""

    tenant = create_tenant(
        database=database,
        name=tenant_data.name,
    )

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        plan=tenant.subscription.plan.name.value,
        status=tenant.subscription.status.value,
    )


@app.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_endpoint(
    usage_data: GenerateRequest,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
    ),
    database: Session = Depends(get_db),
):
    """Record one simulated, billable AI generation."""

    return record_generate_usage(
        database=database,
        tenant_id=usage_data.tenant_id,
        idempotency_key=idempotency_key,
        input_tokens=usage_data.input_tokens,
        cached_input_tokens=usage_data.cached_input_tokens,
        output_tokens=usage_data.output_tokens,
        reasoning_tokens=usage_data.reasoning_tokens,
    )


@app.get(
    "/usage/{tenant_id}",
    response_model=UsageSummaryResponse,
)
def usage_summary_endpoint(
    tenant_id: str,
    database: Session = Depends(get_db),
):
    """Return current monthly usage for one tenant."""

    return get_usage_summary(
        database=database,
        tenant_id=tenant_id,
    )


@app.post(
    "/checkout/{tenant_id}",
    response_model=CheckoutResponse,
)
def checkout_endpoint(
    tenant_id: str,
    database: Session = Depends(get_db),
):
    """Create a Stripe Sandbox Checkout session."""

    return create_checkout_session(
        database=database,
        tenant_id=tenant_id,
    )


@app.post("/webhooks/stripe")
async def stripe_webhook_endpoint(
    request: Request,
    stripe_signature: str = Header(
        ...,
        alias="Stripe-Signature",
    ),
    database: Session = Depends(get_db),
):
    """Verify and process Stripe webhook events."""

    payload = await request.body()

    return process_stripe_webhook(
        database=database,
        payload=payload,
        signature=stripe_signature,
    )