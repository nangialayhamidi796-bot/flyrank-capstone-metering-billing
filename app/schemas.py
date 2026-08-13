from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    """Input required to create a tenant."""

    name: str = Field(
        min_length=2,
        max_length=200,
        examples=["Acme Company"],
    )


class TenantResponse(BaseModel):
    """Information returned after creating a tenant."""

    id: str
    name: str
    plan: str
    status: str