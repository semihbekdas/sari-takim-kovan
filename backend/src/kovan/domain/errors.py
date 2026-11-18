"""Domain hata tipleri.

API katmanı bu hataları tek bir JSON formatına ve HTTP durum koduna çevirir
(docs/architecture.md § 7, docs/api-contract.md "Hata formatı").
"""


class DomainError(Exception):
    """Tüm domain hatalarının temel sınıfı. Varsayılan olarak 422 döner."""

    default_code = "DOMAIN_ERROR"

    def __init__(self, message: str, *, code: str | None = None, rule_code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.rule_code = rule_code


class DomainRuleError(DomainError):
    """Bir domain kuralı ihlal edildi (ör. R-05). API'de 422 döner.

    Kullanım: `DomainRuleError("Döngü oluşur.", rule_code="R-05", code="PAGE_MOVE_CYCLE")`
    """

    default_code = "DOMAIN_RULE_VIOLATION"

    def __init__(self, message: str, *, rule_code: str, code: str | None = None):
        super().__init__(message, code=code, rule_code=rule_code)


class NotFoundError(DomainError):
    """Kaynak yok veya kullanıcıya ait değil. API'de 404 döner."""

    default_code = "NOT_FOUND"


class ConflictError(DomainError):
    """İstek mevcut durumla çakışıyor (ör. sürüm çakışması, R-07). API'de 409 döner."""

    default_code = "CONFLICT"
