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

class GenerateRequest(BaseModel):
    """Simulated AI usage submitted by a tenant."""

    tenant_id: str
    input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)


class GenerateResponse(BaseModel):
    """Result returned after recording a billable action."""

    event_id: str
    tenant_id: str
    idempotency_key: str
    api_calls_used: int
    api_calls_limit: int
    ai_tokens_used: int
    ai_tokens_limit: int
    cost_microcents: int
    duplicate: bool