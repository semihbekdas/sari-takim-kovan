"""Composition root: Adaptörlerin seçilip servislere bağlandığı tek yer (ADR-001).

Çalıştırma:
    uv run uvicorn kovan.main:create_app --factory --reload
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from qdrant_client import QdrantClient

from kovan.api.errors import register_error_handlers
from kovan.api.middleware import register_middleware
from kovan.api.routers import auth, health, pages
from kovan.application.auth_service import SESSION_LIFETIME, AuthService
from kovan.application.health import ReadinessService
from kovan.application.page_service import PageService
from kovan.config import Settings, load_settings
from kovan.container import Container
from kovan.infrastructure.db.engine import create_db_engine
from kovan.infrastructure.db.page_repository import SqlPageTransactions
from kovan.infrastructure.db.probe import DatabaseProbe
from kovan.infrastructure.db.users import SqlUserRepository
from kovan.infrastructure.security.argon2 import Argon2PasswordHasher
from kovan.infrastructure.security.jwt import JwtTokenService
from kovan.infrastructure.vector.qdrant_index import QdrantProbe
from kovan.logging_config import configure_logging

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    configure_logging(settings.log_level)

    engine = create_db_engine(settings.database_url)
    qdrant = QdrantClient(
        url=settings.qdrant_url,
        timeout=settings.qdrant_timeout_seconds,
        check_compatibility=False,  # açılışta Qdrant'a bağlanmaya çalışmasın
    )
    container = Container(
        readiness=ReadinessService([DatabaseProbe(engine), QdrantProbe(qdrant)]),
        auth=AuthService(
            SqlUserRepository(engine),
            Argon2PasswordHasher(),
            JwtTokenService(settings.jwt_secret.get_secret_value(), SESSION_LIFETIME),
        ),
        pages=PageService(SqlPageTransactions(engine)),
        session_cookie_secure=settings.session_cookie_secure,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            try:
                engine.dispose()
            finally:
                qdrant.close()  # veritabanı kapanırken hata olsa bile Qdrant bağlantısı kapanır

    app = FastAPI(
        title="Kovan API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    app.state.container = container
    register_middleware(app)
    register_error_handlers(app)
    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(pages.router, prefix=API_PREFIX)
    return app
