from fastapi import FastAPI

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