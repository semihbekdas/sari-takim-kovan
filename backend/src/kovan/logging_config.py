"""Yapısal (JSON) loglama ayarı.

Her log satırı tek satırlık JSON'dur ve istek içindeyken `request_id` taşır. Bu, hem kendi
kodumuzun (structlog) hem de kütüphanelerin (ör. yapay zeka SDK'ları, uvicorn) standart `logging`
kayıtları için geçerlidir; böylece bütün loglar aynı biçimde okunur ve isteğe bağlanabilir.
"""

import logging
import sys

import structlog
from structlog.tracebacks import ExceptionDictTransformer
from structlog.typing import Processor

# İki log kaynağının (structlog ve standart logging) ortak işlemleri.
_SHARED_PROCESSORS: list[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
]
_RENDERERS: list[Processor] = [
    # Hatanın tipi, mesajı ve satırları loglanır; yerel değişkenler loglanmaz, çünkü
    # şifre, API anahtarı veya istek içeriği taşıyabilirler (KURALLAR.md § 8).
    structlog.processors.ExceptionRenderer(ExceptionDictTransformer(show_locals=False)),
    structlog.processors.JSONRenderer(ensure_ascii=False),
]

# Uvicorn, uygulamayı yüklemeden önce bu logger'lara düz metin yazan kendi handler'larını takar
# ve kayıtları köke iletmez (`propagate=False`).
_UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")


def configure_logging(level: str) -> None:
    numeric_level = logging.getLevelNamesMapping()[level.upper()]
    structlog.configure(
        processors=[*_SHARED_PROCESSORS, *_RENDERERS],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    # Kütüphanelerin standart logging kayıtları da aynı JSON biçiminden geçer.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=[*_SHARED_PROCESSORS, structlog.stdlib.add_logger_name],
            processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, *_RENDERERS],
        )
    )
    logging.basicConfig(handlers=[handler], level=numeric_level, force=True)
    for name in _UVICORN_LOGGERS:
        _route_to_root(logging.getLogger(name))


def _route_to_root(uvicorn_logger: logging.Logger) -> None:
    """Uvicorn'un düz metin handler'larını kaldırır; kayıtlar köke, yani JSON handler'a gider.

    Handler'ı olmayan logger'a dokunulmaz: `--no-access-log` erişim logunu handler'larını
    kaldırıp köke iletmeyerek kapatır; köke bağlamak onu yeniden açardı.
    """
    if not uvicorn_logger.handlers:
        return
    uvicorn_logger.handlers.clear()
    uvicorn_logger.propagate = True
