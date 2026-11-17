"""Hata logları: teşhis için gereken bilgi var, gizli kalması gereken yerel değişkenler yok."""

import pytest
import structlog

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
