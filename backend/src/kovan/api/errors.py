"""Tüm hataların tek bir JSON formatına çevrilmesi (docs/architecture.md § 7).

Format:
    {"error": {"code": "...", "message": "...", "rule": "R-05" | null, "request_id": "..."}}

Stack trace, SQL veya iç hata mesajı istemciye asla gönderilmez; yalnızca loglanır.
"""

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from kovan.api.middleware import REQUEST_ID_HEADER
from kovan.application.errors import ApplicationError, AuthenticationError, ExternalServiceError
from kovan.domain.errors import ConflictError, DomainError, NotFoundError

logger = structlog.get_logger(__name__)

# Sıra önemli: Önce alt sınıflar, sonra temel sınıf.
_STATUS_BY_ERROR_TYPE: tuple[tuple[type[Exception], int], ...] = (
    (NotFoundError, 404),
    (ConflictError, 409),
    (DomainError, 422),
    (AuthenticationError, 401),
    (ExternalServiceError, 503),
)

_HTTP_ERRORS: dict[int, tuple[str, str]] = {
    404: ("NOT_FOUND", "Kaynak bulunamadı."),
    405: ("METHOD_NOT_ALLOWED", "Bu HTTP yöntemi desteklenmiyor."),
}

INTERNAL_ERROR_MESSAGE = "Beklenmeyen bir hata oluştu."

# Pydantic hata tiplerinin kullanıcıya gösterilen Türkçe karşılıkları.
_VALIDATION_MESSAGES: dict[str, str] = {
    "missing": "Bu alan zorunludur.",
    "int_parsing": "Tam sayı olmalıdır.",
    "float_parsing": "Sayı olmalıdır.",
    "bool_parsing": "Doğru veya yanlış olmalıdır.",
    "uuid_parsing": "Geçerli bir kimlik (UUID) olmalıdır.",
    "string_type": "Metin olmalıdır.",
    "string_too_short": "Çok kısa.",
    "string_too_long": "Çok uzun.",
    "greater_than_equal": "İzin verilen en küçük değerin altında.",
    "less_than_equal": "İzin verilen en büyük değerin üstünde.",
    "json_invalid": "Geçerli bir JSON değil.",
}
DEFAULT_VALIDATION_MESSAGE = "Geçersiz değer."


def register_error_handlers(app: FastAPI) -> None:
    # Starlette işleyicileri `Exception` tipiyle çağırır; bu yüzden her işleyici önce
    # beklediği tipi `isinstance` ile doğrular, beklenmeyen tipte genel 500 işleyicisine düşer.
    app.add_exception_handler(DomainError, _handle_known_error)
    app.add_exception_handler(ApplicationError, _handle_known_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)


async def _handle_known_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError | ApplicationError):
        return await _handle_unexpected_error(request, exc)
    status_code = _status_for(exc)
    if status_code is None:
        # Eşlemesi unutulmuş bir hata tipi: programlama hatası gibi ele alınır, ayrıntı sızdırılmaz.
        return await _handle_unexpected_error(request, exc)
    rule = exc.rule_code if isinstance(exc, DomainError) else None
    _log(status_code, exc.code, exc.message)
    return _error_response(request, status_code, exc.code, exc.message, rule=rule)


async def _handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return await _handle_unexpected_error(request, exc)
    # Girilen değer (ör. şifre) yanıta konmaz; yalnızca alan adı ve sorun.
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": _VALIDATION_MESSAGES.get(error["type"], DEFAULT_VALIDATION_MESSAGE),
        }
        for error in exc.errors()
    ]
    _log(422, "VALIDATION_ERROR", "İstek doğrulanamadı.")
    return _error_response(
        request, 422, "VALIDATION_ERROR", "İstek doğrulanamadı.", details=details
    )


async def _handle_http_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        return await _handle_unexpected_error(request, exc)
    if exc.status_code >= 500:
        # Ayrıntı iç bilgi içerebilir: Beklenmeyen hata gibi ele alınır, ayrıntı yalnızca loglanır.
        logger.error("http_server_error", status=exc.status_code, detail=str(exc.detail))
        return _error_response(request, 500, "INTERNAL_ERROR", INTERNAL_ERROR_MESSAGE)
    code, message = _HTTP_ERRORS.get(exc.status_code, ("HTTP_ERROR", str(exc.detail)))
    _log(exc.status_code, code, message)
    response = _error_response(request, exc.status_code, code, message)
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unexpected_error", exc_info=exc)
    return _error_response(request, 500, "INTERNAL_ERROR", INTERNAL_ERROR_MESSAGE)


def _status_for(exc: Exception) -> int | None:
    for error_type, status_code in _STATUS_BY_ERROR_TYPE:
        if isinstance(exc, error_type):
            return status_code
    return None


def _log(status_code: int, code: str, message: str) -> None:
    if status_code >= 500:
        logger.error("request_failed", status=status_code, code=code, message=message)
    elif status_code == 401:
        logger.info("request_rejected", status=status_code, code=code)
    else:
        logger.warning("request_rejected", status=status_code, code=code, message=message)


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    *,
    rule: str | None = None,
    details: list[dict[str, str]] | None = None,
) -> JSONResponse:
    request_id: str | None = getattr(request.state, "request_id", None)
    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "rule": rule,
        "request_id": request_id,
    }
    if details is not None:
        error["details"] = details
    headers = {REQUEST_ID_HEADER: request_id} if request_id else None
    return JSONResponse(status_code=status_code, content={"error": error}, headers=headers)
