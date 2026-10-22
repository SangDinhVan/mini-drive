import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.files import router
from app.core.config import Settings
from app.core.upload_limit import UploadBodyLimit
from app.db.session import build_sessions

logger = logging.getLogger("mini_drive")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app(settings: Settings | None = None, sessions=None):
    settings = settings or Settings.from_env()
    engine = None
    if sessions is None and settings.database_url:
        engine, sessions = build_sessions(settings.database_url)

    @asynccontextmanager
    async def lifespan(app):
        yield
        if engine is not None:
            engine.dispose()

    application = FastAPI(title="Mini Drive", version="1.0.0", lifespan=lifespan)
    application.state.settings = settings
    application.state.sessions = sessions
    application.include_router(router)
    application.add_middleware(UploadBodyLimit, max_bytes=settings.max_upload_mb * 1024 * 1024 + 64 * 1024)

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = uuid4().hex
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error("Unhandled error request_id=%s type=%s", request.state.request_id, type(exc).__name__)
            response = JSONResponse({"detail": "Unexpected server error. Please retry."}, status_code=500)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        logger.info("request_id=%s method=%s status=%s", request.state.request_id, request.method, response.status_code)
        return response

    @application.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        logger.error("Database error request_id=%s type=%s", request.state.request_id, type(exc).__name__)
        return JSONResponse({"detail": "Database unavailable. Check the Neon connection and migrations, then retry."}, status_code=503)

    @application.exception_handler(OSError)
    async def storage_error(request: Request, exc: OSError):
        logger.error("Storage error request_id=%s type=%s", request.state.request_id, type(exc).__name__)
        return JSONResponse({"detail": "Local storage failed. Check disk space and folder permissions, then retry."}, status_code=500)

    @application.get("/api/health", tags=["health"])
    def health():
        return {"status": "ok"}

    return application


app = create_app()
