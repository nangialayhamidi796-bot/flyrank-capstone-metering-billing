from sqlalchemy import select

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Plan, PlanName


def seed_plans() -> None:
    """Create the Free and Pro plans if they do not already exist."""

    Base.metadata.create_all(bind=engine)

    database = SessionLocal()

    try:
        existing_plans = database.scalars(select(Plan)).all()
        existing_names = {plan.name for plan in existing_plans}

        if PlanName.FREE not in existing_names:
            database.add(
                Plan(
                    name=PlanName.FREE,
                    api_call_limit=settings.free_api_call_limit,
                    ai_token_limit=settings.free_ai_token_limit,
                )
            )

        if PlanName.PRO not in existing_names:
            database.add(
                Plan(
                    name=PlanName.PRO,
                    api_call_limit=settings.pro_api_call_limit,
                    ai_token_limit=settings.pro_ai_token_limit,
                )
            )

        database.commit()

    finally:
        database.close()


if __name__ == "__main__":
    seed_plans()
    print("Free and Pro plans seeded successfully.")