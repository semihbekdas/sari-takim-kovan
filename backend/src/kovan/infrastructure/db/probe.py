"""Veritabanının erişilebilir olup olmadığını kontrol eden `ReadinessProbe` uygulaması."""

import structlog
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = structlog.get_logger(__name__)


class DatabaseProbe:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @property
    def name(self) -> str:
        return "database"

    def is_ready(self) -> bool:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError as error:
            # Ayrıntı yalnızca loga yazılır; istemciye sadece "down" bilgisi gider.
            logger.warning("database_unreachable", error_type=type(error).__name__)
            return False
        return True
