from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel

from kovan.application.page_service import PageDetails


class CreatePageRequest(BaseModel):
    # Başlık (R-03) ve içerik (R-06) kuralları domain'de kontrol edilir; şemada tekrarlanmaz.
    title: str | None = None
    parent_id: UUID | None = None
    content: Any = None  # verilmezse boş sayfa


class UpdatePageRequest(BaseModel):
    title: str
    content: Any
    version: int  # istemcinin elindeki sürüm (R-07)


class BreadcrumbResponse(BaseModel):
    id: UUID
    title: str


class PageResponse(BaseModel):
    id: UUID
    parent_id: UUID | None
    title: str
    content: list[dict[str, Any]]
    version: int
    index_status: Literal["INDEXED", "PENDING", "FAILED"]
    breadcrumbs: list[BreadcrumbResponse]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_details(cls, details: PageDetails) -> "PageResponse":
        page = details.page
        return cls(
            id=page.id,
            parent_id=page.parent_id,
            title=page.title,
            content=page.content.blocks,
            version=page.version,
            index_status=page.index_status.value,
            breadcrumbs=[
                BreadcrumbResponse(id=ref.id, title=ref.title) for ref in details.breadcrumbs
            ],
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
