"""Sağlık uç noktaları (docs/api-contract.md "Sağlık"). Oturum gerektirmez."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from kovan.api.deps import get_readiness_service
from kovan.api.schemas.health import HealthResponse, ReadinessResponse
from kovan.application.health import ReadinessService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> HealthResponse:
    """Uygulama ayakta mı? (canlılık)"""
    return HealthResponse()


@router.get("/ready", responses={503: {"model": ReadinessResponse}})
def ready(
    response: Response,
    service: Annotated[ReadinessService, Depends(get_readiness_service)],
) -> ReadinessResponse:
    """Bağımlılıklar (veritabanı vb.) hazır mı?"""
    report = service.check()
    if not report.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse.from_report(report)
