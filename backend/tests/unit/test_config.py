"""Ayarların doğrulanması."""

import pytest
from pydantic import ValidationError

from tests.fakes import make_test_settings


def test_invalid_log_level_stops_startup_with_a_clear_error() -> None:
    with pytest.raises(ValidationError, match="log_level"):
        make_test_settings(log_level="VERBOSE")


@pytest.mark.parametrize("secret", ["", "   ", "kisa-anahtar"])
def test_empty_or_short_jwt_secret_stops_startup(secret: str) -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        make_test_settings(jwt_secret=secret)


def test_jwt_secret_is_hidden_when_settings_are_printed() -> None:
    settings = make_test_settings()

    assert settings.jwt_secret.get_secret_value() not in repr(settings)


def test_chunk_max_chars_defaults_to_1000_and_must_be_positive() -> None:
    assert make_test_settings().chunk_max_chars == 1000
    with pytest.raises(ValidationError, match="chunk_max_chars"):
        make_test_settings(chunk_max_chars=0)
