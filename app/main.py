from fastapi import Depends, FastAPI, status
from sqlalchemy.orm import Session
from app import models

from app.database import Base, engine, get_db
from app.schemas import TenantCreate, TenantResponse
from app.services import create_tenant


Base.metadata.create_all(bind=engine)



app = FastAPI(
    title="Usage Metering and Billing Engine",
    description="API for usage tracking, quota enforcement, and subscription billing.",
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