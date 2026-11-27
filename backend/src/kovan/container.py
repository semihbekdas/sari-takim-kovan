"""Uygulama servislerinin tutulduğu kap.

`main.py` (composition root) doldurur; API katmanı `api/deps.py` üzerinden okur.
Böylece API katmanı infrastructure'ı hiç import etmez (ADR-001).
"""

from dataclasses import dataclass

from kovan.application.auth_service import AuthService
from kovan.application.health import ReadinessService


@dataclass(frozen=True)
class Container:
    readiness: ReadinessService
    auth: AuthService
    # Oturum çerezine `Secure` eklensin mi (ADR-008: prod'da evet).
    session_cookie_secure: bool = False
