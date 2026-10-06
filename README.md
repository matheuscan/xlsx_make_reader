# XLSX Make Reader

API REST con **FastAPI** diseñada para consumirse como **custom app de Make.com**.
Recibe archivos Excel binarios (`.xlsx`/`.xls`), los parsea en memoria y devuelve
cada fila como un bundle dentro de un array de objetos. Gestor de paquetes: **uv**.

## Requisitos

- [uv](https://docs.astral.sh/uv/) instalado
- Python 3.12+ (uv lo gestiona)

## Puesta en marcha

```bash
uv sync
copy .env.example .env        # y edita API_KEY
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- Swagger UI: http://localhost:8000/docs
- Tests: `uv run pytest`

> **Importante para Make**: las custom apps exigen una URL **HTTPS pública**.
> Para probar en local expón el puerto con `ngrok http 8000` o `cloudflared tunnel --url http://localhost:8000`.

## Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/health` | no | Healthcheck |
| GET | `/api/v1/verify` | API Key | Verificación de conexión para Make |
| POST | `/api/v1/parse-excel` | API Key | Parsea el Excel y devuelve `{bundles, meta}` |
| POST | `/api/v1/excel-columns` | API Key | Devuelve las columnas (usado por el RPC de Make) |

Autenticación: header `X-API-Key` (configurable en `.env`).

### POST /api/v1/parse-excel

Acepta el archivo de dos formas:

1. `multipart/form-data` con campo `file` (lo que envía Make)
2. Cuerpo binario raw (`application/octet-stream`)

Query params opcionales:

- `sheet`: nombre o índice (0-based) de la hoja. Por defecto la primera.
- `header_row`: fila usada como cabecera (0-based). Por defecto `0`.

Ejemplo:

```bash
curl -X POST "https://TU-DOMINIO/api/v1/parse-excel?sheet=Clientes" \
  -H "X-API-Key: TU_API_KEY" \
  -F "file=@clientes.xlsx"
```

Respuesta:

```json
{
  "bundles": [
    {"Nombre": "Ana", "Edad": 30, "Ciudad": "Madrid"},
    {"Nombre": "Luis", "Edad": 25, "Ciudad": "Bogotá"}
  ],
  "meta": {
    "sheets": ["Clientes", "Ventas"],
    "sheet": "Clientes",
    "rows": 2,
    "columns": ["Nombre", "Edad", "Ciudad"]
  }
}
```

Códigos de error: `400` archivo no-Excel/vacío, `401` API key inválida,
`404` hoja no encontrada, `413` archivo demasiado grande.

## Custom app de Make

La definición completa está en [`make-app/`](make-app/README.md) (formato Apps SDK).
Incluye:

- Conexión **API Key** (base URL + key, verificada contra `/api/v1/verify`)
- Módulo **Parse Excel File** (tipo *search*): envía el binario como
  `multipart/form-data` con un parámetro `buffer` e itera `body.bundles`,
  de modo que **cada fila del Excel sale como un bundle independiente**
- RPC **get-columns**: genera la interfaz de salida dinámicamente a partir
  de las cabeceras de un archivo de muestra

## Estructura

```
app/
├── main.py            # app FastAPI, CORS, health
├── config.py          # Settings (.env): API_KEY, MAX_FILE_SIZE_MB, CORS_ORIGINS
├── security.py        # dependencia X-API-Key (comparación en tiempo constante)
├── schemas.py         # modelos de respuesta
├── routers/excel.py   # endpoints /api/v1/*
└── services/excel.py  # parseo en memoria con pandas/openpyxl/xlrd
tests/                 # pytest + TestClient
make-app/              # definición de la custom app de Make
```
