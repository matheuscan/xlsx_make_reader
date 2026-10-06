from datetime import datetime
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.config import Settings, get_settings
from app.main import app

TEST_API_KEY = "test-key-123"
AUTH_HEADER = "X-API-Key"


def get_test_settings() -> Settings:
    return Settings(api_key=TEST_API_KEY, max_file_size_mb=20, _env_file=None)


app.dependency_overrides[get_settings] = get_test_settings


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    return {AUTH_HEADER: TEST_API_KEY}


def build_xlsx(sheets: dict[str, list[list]]) -> bytes:
    wb = Workbook()
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(title=name)
        for row in rows:
            ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture()
def sample_xlsx() -> bytes:
    return build_xlsx(
        {
            "Clientes": [
                ["Nombre", "Edad", "Ciudad", "Registro"],
                ["Ana", 30, "Madrid", datetime(2024, 1, 15, 10, 30)],
                ["Luis", 25, None, datetime(2024, 2, 20, 8, 0)],
            ],
            "Ventas": [
                ["ID", "Total"],
                [1, 100.5],
            ],
        }
    )


XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
