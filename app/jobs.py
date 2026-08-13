import logging

from sqlalchemy import select

from app.database import SessionLocal
from app.metering import get_monthly_usage
from app.models import Tenant


logger = logging.getLogger(__name__)


def run_monthly_usage_rollup() -> list[dict]:
    """Calculate current usage summaries for every tenant."""

    database = SessionLocal()
    summaries: list[dict] = []

    try:
        tenant_ids = database.scalars(
            select(Tenant.id)
        ).all()

        for tenant_id in tenant_ids:
            api_calls, ai_tokens, cost = get_monthly_usage(
                database=database,
                tenant_id=tenant_id,
            )

            summaries.append(
                {
                    "tenant_id": tenant_id,
                    "api_calls": api_calls,
                    "ai_tokens": ai_tokens,
                    "cost_microcents": cost,
                }
            )

        logger.info(
            "Monthly usage rollup completed for %s tenants.",
            len(summaries),
        )

        return summaries

    except Exception:
        logger.exception(
            "Monthly usage rollup failed."
        )
        raise

    finally:
        database.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    rollups = run_monthly_usage_rollup()

    print(
        f"Usage rollup completed for {len(rollups)} tenants."
    )