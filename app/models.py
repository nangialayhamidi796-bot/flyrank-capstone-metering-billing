import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    """Return the current time in UTC."""

    return datetime.now(timezone.utc)


class PlanName(str, enum.Enum):
    FREE = "free"
    PRO = "pro"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class UsageType(str, enum.Enum):
    API_CALL = "api_call"
    AI_TOKENS = "ai_tokens"

class Plan(Base):
    """A subscription plan and its monthly usage limits."""

    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[PlanName] = mapped_column(
        Enum(PlanName),
        unique=True,
        nullable=False,
    )
    api_call_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    ai_token_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="plan"
    )


class Tenant(Base):
    """A customer organization using the service."""

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    subscription: Mapped["Subscription"] = relationship(
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan",
    )
    usage_events: Mapped[list["UsageEvent"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

class Subscription(Base):
    """A tenant's current subscription and payment status."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("plans.id"),
        nullable=False,
        index=True,
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
    )
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    tenant: Mapped["Tenant"] = relationship(
        back_populates="subscription"
    )
    plan: Mapped["Plan"] = relationship(
        back_populates="subscriptions"
    )

class UsageEvent(Base):
    """One billable action recorded for a tenant."""

    __tablename__ = "usage_events"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_usage_tenant_idempotency_key",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    usage_type: Mapped[UsageType] = mapped_column(
        Enum(UsageType),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    request_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    input_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    cached_input_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    output_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    reasoning_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    cost_microcents: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    tenant: Mapped["Tenant"] = relationship(
        back_populates="usage_events"
    )
class StripeEvent(Base):
    """A processed Stripe webhook event."""

    __tablename__ = "stripe_events"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )