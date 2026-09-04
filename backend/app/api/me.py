from fastapi import APIRouter, Depends

from app.auth.principal import Principal, get_current_principal

router = APIRouter(prefix="/api/v1", tags=["identity"])


@router.get("/me")
async def get_me(principal: Principal = Depends(get_current_principal)) -> dict[str, object]:
    return {"id": principal.subject, "claims": principal.claims}
