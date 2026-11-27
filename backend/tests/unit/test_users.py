import pytest

from kovan.domain.errors import DomainRuleError
from kovan.domain.users import check_password_length, normalize_email


def test_email_is_trimmed_and_lowercased() -> None:
    assert normalize_email("  Ayse@Ornek.COM ") == "ayse@ornek.com"


@pytest.mark.ac("AC-01.3")
@pytest.mark.parametrize(
    "email",
    [
        "",
        "ayse",
        "ayse@",
        "@ornek.com",
        "ayse@ornek",
        "a b@ornek.com",
        "a@b@ornek.com",
        "ayse@.com",
        "ayse@ornek.",
    ],
)
def test_invalid_email_is_rejected_with_r01(email: str) -> None:
    with pytest.raises(DomainRuleError) as error:
        normalize_email(email)

    assert error.value.rule_code == "R-01"
    assert error.value.code == "EMAIL_INVALID"


def test_too_long_email_is_rejected() -> None:
    with pytest.raises(DomainRuleError):
        normalize_email("a" * 250 + "@ornek.com")


@pytest.mark.parametrize("password", ["a" * 8, "a" * 128])
def test_password_within_limits_is_accepted(password: str) -> None:
    check_password_length(password)  # hata fırlatmamalı

    assert len(password) in (8, 128)


@pytest.mark.ac("AC-01.3")
@pytest.mark.parametrize(
    ("password", "code"),
    [("a" * 7, "PASSWORD_TOO_SHORT"), ("a" * 129, "PASSWORD_TOO_LONG")],
)
def test_password_outside_limits_is_rejected_with_r02(password: str, code: str) -> None:
    with pytest.raises(DomainRuleError) as error:
        check_password_length(password)

    assert error.value.rule_code == "R-02"
    assert error.value.code == code
