from math import ceil

from fastapi import HTTPException


def page_values(page: int, page_size: int) -> tuple[int, int, int]:
    if page < 1:
        raise HTTPException(status_code=422, detail="page must be at least 1")
    if not 1 <= page_size <= 100:
        raise HTTPException(status_code=422, detail="page_size must be between 1 and 100")
    return page, page_size, (page - 1) * page_size


def pages(total: int, page_size: int) -> int:
    return ceil(total / page_size) if total else 0
