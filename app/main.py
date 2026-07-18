import logging
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.routers import applications, deployments
from app import models  # noqa: F401

# Setup logging configuration
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(levelname)-5s shiptrack: %(message)s",
)
logger = logging.getLogger("shiptrack")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup
    Base.metadata.create_all(bind=engine)
    logger.info(f"ShipTrack API starting, env={settings.APP_ENV}, db=connected")
    yield


app = FastAPI(
    title="ShipTrack API",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(applications.router)
app.include_router(deployments.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = exc.errors()
    if errors:
        err = errors[0]
        # Format the field location path, e.g. "body.version"
        loc = ".".join(str(item) for item in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        # Clean up custom raised ValidationError text
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        message = f"{loc}: {msg}"
    else:
        message = "Validation error"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": message,
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        code = detail["code"]
        message = detail["message"]
    else:
        # Default fallback
        code = "error"
        message = str(detail)
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "unauthorized"
            if message == "Not authenticated":
                message = "Missing X-API-Key header"
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "not_found"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": message,
            }
        },
    )


@app.get("/health", status_code=status.HTTP_200_OK, summary="Liveness + DB check")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database": "unavailable"},
        )