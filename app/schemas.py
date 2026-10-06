from typing import Any

from pydantic import BaseModel


class ParseMeta(BaseModel):
    sheets: list[str]
    sheet: str
    rows: int
    columns: list[str]


class ParseExcelResponse(BaseModel):
    bundles: list[dict[str, Any]]
    meta: ParseMeta


class ColumnsResponse(BaseModel):
    columns: list[str]
    sheets: list[str]
    sheet: str
