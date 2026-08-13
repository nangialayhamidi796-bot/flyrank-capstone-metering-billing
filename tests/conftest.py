import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Plan, PlanName


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    """Create an isolated in-memory database for the test suite."""

    Base.metadata.create_all(bind=test_engine)

    database = TestingSessionLocal()

    database.add_all(
        [
            Plan(
                name=PlanName.FREE,
                api_call_limit=1000,
                ai_token_limit=100_000,
            ),
            Plan(
                name=PlanName.PRO,
                api_call_limit=10_000,
                ai_token_limit=1_000_000,
            ),
        ]
    )
    database.commit()
    database.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    """Give API tests a session connected to the test database."""

    database = TestingSessionLocal()

    try:
        yield database
    finally:
        database.close()


app.dependency_overrides[get_db] = override_get_db