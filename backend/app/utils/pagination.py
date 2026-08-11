from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.schemas.common import Page


def paginate(
    db: Session,
    query: Select,
    page: int,
    page_size: int,
    *,
    count_source: Select | None = None,
) -> Page:
    source = count_source if count_source is not None else query
    total = db.scalar(select(func.count()).select_from(source.subquery())) or 0
    rows = db.execute(query.offset((page - 1) * page_size).limit(page_size)).all()
    return Page(
        items=rows,
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )
