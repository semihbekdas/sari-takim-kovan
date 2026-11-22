"""Hata logları: teşhis için gereken bilgi var, gizli kalması gereken yerel değişkenler yok."""

import json
import logging

import pytest
import structlog
import uvicorn

from kovan.logging_config import configure_logging

API_KEY = "sk-test-gizli-anahtar"


def _call_provider(api_key: str) -> None:
    raise RuntimeError("Sağlayıcıya bağlanılamadı.")


def test_exception_log_keeps_the_error_but_not_local_variables(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("INFO")

    try:
        _call_provider(API_KEY)
    except RuntimeError:
        structlog.get_logger("test").exception("provider_failed")

    log_line = capsys.readouterr().out
    assert "Sağlayıcıya bağlanılamadı." in log_line
    assert "_call_provider" in log_line
    assert API_KEY not in log_line


def test_library_logs_are_json_with_the_request_id(capsys: pytest.CaptureFixture[str]) -> None:
    # Ör. yapay zeka SDK'ları httpx üzerinden standart logging ile "HTTP Request: ..." yazar.
    configure_logging("INFO")
    structlog.contextvars.bind_contextvars(request_id="istek-1")
    try:
        logging.getLogger("httpx").info("HTTP Request: POST https://api.example.test")
    finally:
        structlog.contextvars.clear_contextvars()

    record = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert record["event"] == "HTTP Request: POST https://api.example.test"
    assert record["request_id"] == "istek-1"
    assert (record["level"], record["logger"]) == ("info", "httpx")


def _start_uvicorn_logging(*, access_log: bool = True) -> None:
    """`uv run uvicorn ...` gibi, uygulama yüklenmeden önce uvicorn'un kendi log ayarını kurar.

    Ayarı uvicorn'un `Config` sınıfı oluşturulurken uygular: `uvicorn` ve `uvicorn.access`
    logger'larına düz metin yazan handler'lar takar ve kayıtları köke iletmez.
    """
    uvicorn.Config("kovan.main:create_app", factory=True, access_log=access_log)


def test_uvicorn_logs_are_json_too(capsys: pytest.CaptureFixture[str]) -> None:
    _start_uvicorn_logging()
    configure_logging("INFO")

    logging.getLogger("uvicorn.error").info("Application startup complete.")
    access = ("127.0.0.1:5000", "GET", "/health/live", "1.1", 200)
    logging.getLogger("uvicorn.access").info('%s - "%s %s HTTP/%s" %d', *access)

    output = capsys.readouterr()
    records = [json.loads(line) for line in output.out.strip().splitlines()]
    assert [record["logger"] for record in records] == ["uvicorn.error", "uvicorn.access"]
    assert output.err == ""


def test_disabled_uvicorn_access_log_stays_disabled() -> None:
    # `--no-access-log`: Uvicorn erişim logger'ının handler'larını kaldırır ve köke iletmez.
    _start_uvicorn_logging(access_log=False)
    configure_logging("INFO")

    # Uvicorn, erişim logu yazıp yazmayacağına bu kontrolle karar verir.
    assert not logging.getLogger("uvicorn.access").hasHandlers()
