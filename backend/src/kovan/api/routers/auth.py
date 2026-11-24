"""Kimlik uç noktaları (docs/api-contract.md "Kimlik"). Kayıt oturum gerektirmez."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from kovan.api.deps import get_auth_service
from kovan.api.schemas.auth import RegisterRequest, UserResponse
from kovan.application.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


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
