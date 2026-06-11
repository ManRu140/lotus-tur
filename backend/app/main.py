import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.routes import admin, auth, bookings, notifications, profile, promo, tours
from app.core.config import settings
from app.db.session import init_db
from app.middleware.csrf import CSRFMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

logging.basicConfig(
    level=logging.INFO if settings.ENV != "development" else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("lotos_tour")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения, инициализация БД...")
    await init_db()
    logger.info("БД готова. Сервис запущен.")
    yield
    logger.info("Завершение работы сервиса.")


_docs_url  = "/docs"  if settings.ENV != "production" else None
_redoc_url = "/redoc" if settings.ENV != "production" else None

app = FastAPI(
    title="Лотос Тур API",
    description="Backend для туристического сайта «Пора в поход»",
    version="1.1.0",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url="/openapi.json" if settings.ENV != "production" else None,
)


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)

app.add_middleware(GZipMiddleware, minimum_size=1024)

if settings.ENV == "production":


    allowed_hosts = getattr(settings, "ALLOWED_HOSTS", None) or [
        "lotus-tur-production-23c6.up.railway.app",
    ]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-CSRF-Token"],
    expose_headers=["X-CSRF-Token"],
    max_age=600,
)

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning("IntegrityError на %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Запись с такими данными уже существует"},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    logger.error("SQLAlchemyError на %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера, попробуйте позже"},
    )


app.include_router(auth.router,          prefix="/api/auth",          tags=["Auth"])
app.include_router(tours.router,         prefix="/api/tours",         tags=["Tours"])
app.include_router(bookings.router,      prefix="/api/bookings",      tags=["Bookings"])
app.include_router(profile.router,       prefix="/api/profile",       tags=["Profile"])
app.include_router(promo.router,         prefix="/api/promo",         tags=["Promo"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(admin.router,         prefix="/api/admin",         tags=["Admin"])


@app.get("/", tags=["Health"], include_in_schema=False)
async def root():
    return {"status": "ok", "service": "Лотос Тур API"}


@app.get("/api/health", tags=["Health"], summary="Healthcheck")
async def health_check():

    if settings.ENV == "production":
        return {"status": "ok"}
    return {
        "status": "ok",
        "service": "Лотос Тур API",
        "version": "1.1.0",
        "env": settings.ENV,
    }
