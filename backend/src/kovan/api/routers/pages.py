"""Sayfa uç noktaları (docs/api-contract.md "Sayfalar"). Hepsi oturum ister (401)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from kovan.api.deps import CurrentUser, get_page_service
from kovan.api.schemas.pages import CreatePageRequest, PageResponse
from kovan.application.page_service import PageService

router = APIRouter(prefix="/pages", tags=["pages"])

Service = Annotated[PageService, Depends(get_page_service)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_page(body: CreatePageRequest, user: CurrentUser, service: Service) -> PageResponse:
    """Yeni sayfa (US-03); `parent_id` verilirse alt sayfa olur (US-05)."""
    details = service.create(
        owner_id=user.id, title=body.title, parent_id=body.parent_id, content=body.content
    )
    return PageResponse.from_details(details)


@router.get("/{page_id}")
def get_page(page_id: UUID, user: CurrentUser, service: Service) -> PageResponse:
    """Kendi sayfası; başkasınınsa veya yoksa 404 (AC-03.3, AC-03.4)."""
    return PageResponse.from_details(service.get(owner_id=user.id, page_id=page_id))
