"""FastAPI bağımlılıkları: Router'lar servislere buradan ulaşır.

Testlerde `app.dependency_overrides` ile fake servisler verilebilir.
"""

from typing import Annotated, cast

from fastapi import Depends, Request

from kovan.application.auth_service import AuthService
from kovan.application.health import ReadinessService
from kovan.container import Container
from kovan.domain.users import User

# ADR-008: Oturum token'ını taşıyan çerez.
SESSION_COOKIE_NAME = "kovan_session"


def get_container(request: Request) -> Container:
    return cast(Container, request.app.state.container)


def get_readiness_service(
    container: Annotated[Container, Depends(get_container)],
) -> ReadinessService:
    return container.readiness


def get_auth_service(
    container: Annotated[Container, Depends(get_container)],
) -> AuthService:
    return container.auth


def get_current_user(
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """İsteği atan kullanıcıyı çerezden çözer; oturum yoksa veya geçersizse 401 (AC-02.4).

    Korumalı her uç nokta bunu `CurrentUser` olarak ister.
    """
    return service.current_user(request.cookies.get(SESSION_COOKIE_NAME))


CurrentUser = Annotated[User, Depends(get_current_user)]
