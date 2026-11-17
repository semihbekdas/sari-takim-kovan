"""Yapısal (JSON) loglama ayarı (Bölüm 4).

Her log satırı tek satırlık JSON'dur ve istek içindeyken `request_id` taşır.
"""

import logging
import sys

import structlog
from structlog.tracebacks import ExceptionDictTransformer


def configure_logging(level: str) -> None:
    numeric_level = logging.getLevelNamesMapping()[level.upper()]
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=numeric_level, force=True)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # Hatanın tipi, mesajı ve satırları loglanır; yerel değişkenler loglanmaz, çünkü
            # şifre, API anahtarı veya istek içeriği taşıyabilirler (KURALLAR.md § 8).
            structlog.processors.ExceptionRenderer(ExceptionDictTransformer(show_locals=False)),
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
