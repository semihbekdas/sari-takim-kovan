from kovan.application.errors import ExternalServiceError
from kovan.domain.errors import DomainRuleError, NotFoundError


def test_domain_rule_error_carries_rule_code_and_default_code() -> None:
    error = DomainRuleError("R-05", "Döngü oluşur.")

    assert error.rule_code == "R-05"
    assert error.code == "DOMAIN_RULE_VIOLATION"
    assert error.message == "Döngü oluşur."


def test_specific_code_overrides_default_code() -> None:
    assert NotFoundError("Sayfa yok.", code="PAGE_NOT_FOUND").code == "PAGE_NOT_FOUND"
    assert ExternalServiceError("Kapalı.", code="AI_SERVICE_UNAVAILABLE").code == (
        "AI_SERVICE_UNAVAILABLE"
    )
