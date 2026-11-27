"""Kimlik uç noktaları (docs/api-contract.md "Kimlik"). Kayıt, giriş ve çıkış oturum gerektirmez."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from kovan.api.deps import SESSION_COOKIE_NAME, CurrentUser, get_auth_service, get_container
from kovan.api.schemas.auth import LoginRequest, RegisterRequest, UserResponse
from kovan.application.auth_service import SESSION_LIFETIME, AuthService
from kovan.container import Container

router = APIRouter(prefix="/auth", tags=["auth"])

# ADR-008: Çerez yalnızca API isteklerinde gönderilir ve JS'ten okunamaz.
SESSION_COOKIE_PATH = "/api"


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Yeni hesap açar (US-01). E-posta kayıtlıysa 409, kural ihlalinde 422."""
    user = service.register(
        email=body.email, password=body.password, display_name=body.display_name
    )
    return UserResponse.from_user(user)


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
def login(
    body: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    container: Annotated[Container, Depends(get_container)],
) -> Response:
    """Giriş yapar ve oturum çerezini verir (AC-02.1). Bilgiler yanlışsa genel 401 (AC-02.2)."""
    token = service.login(email=body.email, password=body.password)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        path=SESSION_COOKIE_PATH,
        secure=container.session_cookie_secure,
        httponly=True,
        samesite="strict",
    )
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(container: Annotated[Container, Depends(get_container)]) -> Response:
    """Oturum çerezini siler (AC-02.3). Oturum olmasa da 204 döner."""
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path=SESSION_COOKIE_PATH,
        secure=container.session_cookie_secure,
        httponly=True,
        samesite="strict",
    )
    return response


@router.get("/me")
def me(user: CurrentUser) -> UserResponse:
    """Oturumdaki kullanıcıyı döner (AC-02.1); oturum yoksa 401 (AC-02.4)."""
    return UserResponse.from_user(user)
