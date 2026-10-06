from datetime import date, datetime, time
from io import BytesIO
from pathlib import PurePath
from typing import Any

import pandas as pd

ALLOWED_EXTENSIONS = {".xlsx", ".xls"}


class ExcelError(Exception):
    """Error base al parsear el archivo Excel."""


class UnsupportedFileError(ExcelError):
    """El archivo no es un Excel válido o la extensión no está soportada."""


class SheetNotFoundError(ExcelError):
    """La hoja solicitada no existe en el libro."""


def validate_filename(filename: str | None) -> None:
    if not filename:
        return
    suffix = PurePath(filename).suffix.lower()
    if suffix and suffix not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileError(f"Extensión '{suffix}' no soportada. Usa .xlsx o .xls")


def _jsonable(value: Any) -> Any:
    if value is None or value is pd.NA:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    return value


def _resolve_sheet(names: list[str], sheet: str | None) -> str:
    if sheet is None:
        return names[0]
    if sheet in names:
        return sheet
    try:
        index = int(sheet)
    except ValueError:
        raise SheetNotFoundError(f"Hoja '{sheet}' no encontrada. Disponibles: {names}")
    if not 0 <= index < len(names):
        raise SheetNotFoundError(f"Índice de hoja {index} fuera de rango. Disponibles: {names}")
    return names[index]


def open_workbook(data: bytes, filename: str | None = None) -> pd.ExcelFile:
    validate_filename(filename)
    if not data:
        raise UnsupportedFileError("Archivo vacío")
    try:
        return pd.ExcelFile(BytesIO(data))
    except ExcelError:
        raise
    except Exception as exc:
        raise UnsupportedFileError(f"No se pudo leer el archivo como Excel: {exc}") from exc


def parse_excel(
    data: bytes,
    sheet: str | None = None,
    header_row: int = 0,
    filename: str | None = None,
) -> dict[str, Any]:
    workbook = open_workbook(data, filename)
    names = workbook.sheet_names
    target = _resolve_sheet(names, sheet)
    df = workbook.parse(sheet_name=target, header=header_row)
    df.columns = [str(c) for c in df.columns]
    bundles = [
        {col: _jsonable(val) for col, val in zip(df.columns, record)}
        for record in df.itertuples(index=False, name=None)
    ]
    return {
        "bundles": bundles,
        "meta": {
            "sheets": names,
            "sheet": target,
            "rows": len(bundles),
            "columns": list(df.columns),
        },
    }


def read_columns(
    data: bytes,
    sheet: str | None = None,
    header_row: int = 0,
    filename: str | None = None,
) -> dict[str, Any]:
    workbook = open_workbook(data, filename)
    names = workbook.sheet_names
    target = _resolve_sheet(names, sheet)
    df = workbook.parse(sheet_name=target, header=header_row, nrows=1)
    return {
        "columns": [str(c) for c in df.columns],
        "sheets": names,
        "sheet": target,
    }
