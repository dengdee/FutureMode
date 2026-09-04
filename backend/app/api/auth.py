from fastapi import APIRouter, Depends

from app.config import Settings, get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.get("/config")
async def auth_config(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    """Return public Auth configuration; never expose secrets or signing keys."""
    return {
        "provider": "neon_auth",
        "configured": settings.neon_auth_configured,
        "base_url": settings.neon_auth_base_url,
        "issuer": settings.neon_auth_issuer,
    }
