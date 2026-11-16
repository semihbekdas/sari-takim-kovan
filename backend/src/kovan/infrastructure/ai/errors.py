"""Yapay zeka SDK hatalarının `ExternalServiceError`'a çevrilmesi (translate at boundaries).

SDK'lar zaman aşımı, 429 ve 5xx hatalarında zaten kendileri yeniden dener; buraya gelen hata
yeniden denemelerden sonra kalan hatadır. İstemciye ayrıntı gitmez, yalnızca loglanır.
"""

from collections.abc import Sequence

import structlog

from kovan.application.errors import ExternalServiceError

AI_SERVICE_UNAVAILABLE = "AI_SERVICE_UNAVAILABLE"
AI_SERVICE_MESSAGE = "Yapay zeka servisine şu an ulaşılamıyor."

logger = structlog.get_logger(__name__)


def to_external_error(
    error: Exception, *, provider: str, reasons: Sequence[tuple[type[Exception], str]]
) -> ExternalServiceError:
    """Hatayı sınıflandırıp loglar ve kullanıcıya gösterilecek hataya çevirir."""
    reason = next((name for error_type, name in reasons if isinstance(error, error_type)), "other")
    logger.warning(
        "ai_provider_error",
        provider=provider,
        reason=reason,
        status_code=getattr(error, "status_code", None),
    )
    return ExternalServiceError(AI_SERVICE_MESSAGE, code=AI_SERVICE_UNAVAILABLE)
