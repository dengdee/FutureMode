import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.consensus import router as consensus_router
from app.api.delegates import router as delegates_router
from app.api.documents import router as documents_router
from app.api.me import router as identity_router
from app.api.meetings import router as meetings_router
from app.api.personal import router as personal_router
from app.api.suggestions import router as suggestions_router
from app.api.teams import router as teams_router
from app.api.transcripts import router as transcripts_router
from app.config import get_settings
from app.db.session import database_check
from app.api.meetbot import router as meetbot_router
from app.websocket.events import router as realtime_events_router

settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("proximate.api")

app = FastAPI(
    title="Proximate API",
    version="0.1.0",
    description="Initial API scaffold. No product features are implemented.",
)
app.state.settings = settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id

    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request failure", extra={"request_id": request_id})
        response = JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "服務暫時無法處理請求",
                    "request_id": request_id,
                }
            },
        )

    response.headers["X-Request-ID"] = request_id
    return response


def error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request.state.request_id,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, _: RequestValidationError):
    return error_response(request, 422, "validation_error", "請求資料格式錯誤")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    status_messages = {
        400: "請求無效",
        401: "需要驗證身份",
        403: "沒有執行此操作的權限",
        404: "找不到資源",
        409: "資源狀態衝突",
        422: "請求資料格式錯誤",
        502: "外部服務暫時無法使用",
    }
    status_code = exc.status_code
    message = status_messages.get(status_code, "服務暫時無法處理請求")
    code = "http_error" if status_code < 500 else "upstream_error"
    return error_response(request, status_code, code, message)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/ready", tags=["system"])
async def ready() -> dict[str, object]:
    db_status = await database_check(settings)
    return {
        "status": "ok" if db_status in {"ok", "not_configured"} else "degraded",
        "environment": settings.app_env,
        "checks": {
            "api": "ok",
            "database": db_status,
            "meeting_baas": "configured" if settings.meeting_baas_api_key else "not_configured",
        },
    }


app.include_router(meetbot_router)
app.include_router(identity_router)
app.include_router(auth_router)
app.include_router(teams_router)
app.include_router(transcripts_router)
app.include_router(consensus_router)
app.include_router(delegates_router)
app.include_router(documents_router)
app.include_router(personal_router)
app.include_router(suggestions_router)
app.include_router(meetings_router)
app.include_router(realtime_events_router)
