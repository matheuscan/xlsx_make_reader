from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status

from app.config import Settings, get_settings
from app.schemas import ColumnsResponse, ParseExcelResponse
from app.security import require_api_key
from app.services.excel import SheetNotFoundError, UnsupportedFileError, parse_excel, read_columns

router = APIRouter(prefix="/api/v1", tags=["excel"], dependencies=[Depends(require_api_key)])

EXCEL_MEDIA_TYPES = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
)


async def _read_upload(
    request: Request,
    file: UploadFile | None,
    settings: Settings,
) -> tuple[bytes, str | None]:
    if file is not None:
        data = await file.read()
        filename = file.filename
    else:
        data = await request.body()
        filename = None
    if len(data) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el límite de {settings.max_file_size_mb} MB",
        )
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuerpo vacío: no se recibió ningún archivo")
    return data, filename


def _map_excel_errors(exc: Exception) -> HTTPException:
    if isinstance(exc, SheetNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, UnsupportedFileError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/verify")
def verify() -> dict[str, str]:
    """Endpoint ligero protegido por API key. Make lo usa para verificar la conexión."""
    return {"status": "ok"}


@router.post("/parse-excel", response_model=ParseExcelResponse)
async def post_parse_excel(
    request: Request,
    settings: Settings = Depends(get_settings),
    file: UploadFile | None = File(default=None, description="Archivo Excel (.xlsx/.xls)"),
    sheet: str | None = Query(default=None, description="Nombre o índice (0-based) de la hoja. Por defecto la primera."),
    header_row: int = Query(default=0, ge=0, description="Fila usada como cabecera (0-based)"),
) -> ParseExcelResponse:
    """Recibe un Excel binario (multipart/form-data o raw body) y devuelve cada fila como un bundle."""
    data, filename = await _read_upload(request, file, settings)
    try:
        result = parse_excel(data, sheet=sheet, header_row=header_row, filename=filename)
    except Exception as exc:
        raise _map_excel_errors(exc) from exc
    return ParseExcelResponse(**result)


@router.post("/excel-columns", response_model=ColumnsResponse)
async def post_excel_columns(
    request: Request,
    settings: Settings = Depends(get_settings),
    file: UploadFile | None = File(default=None, description="Archivo Excel (.xlsx/.xls) de muestra"),
    sheet: str | None = Query(default=None, description="Nombre o índice (0-based) de la hoja."),
    header_row: int = Query(default=0, ge=0, description="Fila usada como cabecera (0-based)"),
) -> ColumnsResponse:
    """Devuelve los nombres de columna de una hoja. Usado por el RPC de campos dinámicos de Make."""
    data, filename = await _read_upload(request, file, settings)
    try:
        result = read_columns(data, sheet=sheet, header_row=header_row, filename=filename)
    except Exception as exc:
        raise _map_excel_errors(exc) from exc
    return ColumnsResponse(**result)
