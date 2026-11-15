"""Yapısal (JSON) loglama ayarı (Bölüm 4).

Her log satırı tek satırlık JSON'dur ve istek içindeyken `request_id` taşır.
"""

import logging
import sys

import structlog


def configure_logging(level: str) -> None:
    numeric_level = logging.getLevelNamesMapping()[level.upper()]
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=numeric_level, force=True)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
