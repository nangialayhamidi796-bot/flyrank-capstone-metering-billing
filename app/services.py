from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Plan,
    PlanName,
    Subscription,
    SubscriptionStatus,
    Tenant,
)


def create_tenant(database: Session, name: str) -> Tenant:
    """Create a tenant and assign the Free plan."""

    free_plan = database.scalar(
        select(Plan).where(Plan.name == PlanName.FREE)
    )

    if free_plan is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Free plan is missing. Run the seed command first.",
        )

    tenant = Tenant(name=name.strip())

    tenant.subscription = Subscription(
        plan=free_plan,
        status=SubscriptionStatus.ACTIVE,
    )

    database.add(tenant)
    database.commit()
    database.refresh(tenant)

    return tenant