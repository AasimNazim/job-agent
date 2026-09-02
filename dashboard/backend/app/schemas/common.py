from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

ItemT = TypeVar("ItemT")


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int


class PaginatedResponse(BaseModel, Generic[ItemT]):
    items: list[ItemT]
    page: int
    page_size: int
    total: int
    pages: int


def pagination(page: int, page_size: int, total: int) -> Pagination:
    return Pagination(page=page, page_size=page_size, total=total, pages=ceil(total / page_size) if total else 0)
