"""FastAPI bağımlılıkları: Router'lar servislere buradan ulaşır.

Testlerde `app.dependency_overrides` ile fake servisler verilebilir.
"""

from typing import Annotated, cast

from fastapi import Depends, Request

from kovan.application.auth_service import AuthService
from kovan.application.health import ReadinessService
from kovan.container import Container


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
