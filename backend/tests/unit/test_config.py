"""Ayarların doğrulanması."""

import pytest
from pydantic import ValidationError

from tests.fakes import make_test_settings


def test_invalid_log_level_stops_startup_with_a_clear_error() -> None:
    with pytest.raises(ValidationError, match="log_level"):
        make_test_settings(log_level="VERBOSE")
