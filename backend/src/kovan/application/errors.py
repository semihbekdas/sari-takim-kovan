"""Uygulama katmanı hata tipleri.

Domain kuralıyla ilgili olmayan, akışa ait hatalar burada tanımlanır.
"""


class ApplicationError(Exception):
    """Uygulama hatalarının temel sınıfı."""

    default_code = "APPLICATION_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code


class AuthenticationError(ApplicationError):
    """Oturum yok, geçersiz veya süresi dolmuş. API'de 401 döner."""

    default_code = "UNAUTHENTICATED"


class ExternalServiceError(ApplicationError):
    """Dış servis (yapay zeka API'si, Qdrant vb.) geçici olarak kullanılamıyor. API'de 503 döner.

    Adaptörler, dış kütüphanelerin hatalarını bu tipe çevirir (translate at boundaries).
    """

    default_code = "EXTERNAL_SERVICE_UNAVAILABLE"
