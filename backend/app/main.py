import logging
import asyncio
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
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
from app.realtime.rooms import RoomRegistry
from app.realtime.events import EventJournal
from app.realtime.persistence import PostgresEventJournal
from app.realtime.broker import RedisRealtimeBroker
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
app.state.room_registry = RoomRegistry()
app.state.event_journal = (
    PostgresEventJournal(settings) if settings.database_configured else EventJournal()
)
app.state.realtime_broker = (
    RedisRealtimeBroker(settings.upstash_redis_url) if settings.realtime_broker_configured else None
)
app.state.realtime_broker_task = None


async def _relay_broker_events() -> None:
    """Forward other Vercel instances' events to this instance's local sockets."""
    broker = app.state.realtime_broker
    if broker is None:
        return
    async for broker_event in broker.subscribe():
        await app.state.room_registry.publish(
            broker_event.event, recipient_user_id=broker_event.recipient_user_id
        )


@app.on_event("startup")
async def start_realtime_broker() -> None:
    if app.state.realtime_broker is not None:
        app.state.realtime_broker_task = asyncio.create_task(_relay_broker_events())


@app.on_event("shutdown")
async def stop_realtime_broker() -> None:
    task = app.state.realtime_broker_task
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    if app.state.realtime_broker is not None:
        await app.state.realtime_broker.close()


def custom_openapi() -> dict[str, object]:
    """Expose the existing JWT bearer header in Swagger UI."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    components = schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Paste a valid Neon Auth access token.",
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

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
    if status_code == 403:
        invitation_errors = {
            "invitation_identity_email_missing": (
                "invitation_email_missing", "登入驗證資料未包含 Email，無法配對站內邀請。"
            ),
            "invitation_identity_email_unverified": (
                "invitation_email_unverified", "登入帳號的 Email 尚未驗證，無法領取站內邀請。"
            ),
        }
        if isinstance(exc.detail, str) and exc.detail in invitation_errors:
            code, message = invitation_errors[exc.detail]
            logger.info("invitation_access_denied reason=%s", code)
    if status_code == 503:
        known_failures = {
            "authentication service unavailable": (
                "auth_unavailable", "登入驗證服務暫時無法連線，請稍後重試。"
            ),
            "database is unavailable": (
                "database_unavailable", "資料庫暫時無法連線，請稍後重試。"
            ),
            "JWT authentication is not configured": (
                "auth_not_configured", "登入驗證設定尚未完成。"
            ),
        }
        code, message = known_failures.get(str(exc.detail), (code, message))
    return error_response(request, status_code, code, message)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/ready", tags=["system"])
async def ready() -> dict[str, object]:
    db_status = await database_check(settings)
    broker_ready = not settings.realtime_require_broker or settings.realtime_broker_configured
    return {
        "status": "ok" if db_status in {"ok", "not_configured"} and broker_ready else "degraded",
        "environment": settings.app_env,
        "checks": {
            "api": "ok",
            "database": db_status,
            "meeting_baas": "configured" if settings.meeting_baas_api_key else "not_configured",
            "realtime_broker": "configured"
            if settings.realtime_broker_configured
            else "not_configured",
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
