from fastapi import FastAPI

from app.config import get_settings
from app.meetbot import router as meetbot_router

settings = get_settings()

app = FastAPI(
    title="Proximate API",
    version="0.1.0",
    description="Initial API scaffold. No product features are implemented.",
)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


app.include_router(meetbot_router)
