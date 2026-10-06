from tests.conftest import AUTH_HEADER, TEST_API_KEY, XLSX_MEDIA

URL = "/api/v1/parse-excel"
COLUMNS_URL = "/api/v1/excel-columns"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_missing_api_key(client, sample_xlsx):
    r = client.post(URL, files={"file": ("clientes.xlsx", sample_xlsx, XLSX_MEDIA)})
    assert r.status_code == 401


def test_wrong_api_key(client, sample_xlsx):
    r = client.post(URL, headers={AUTH_HEADER: "wrong"}, files={"file": ("clientes.xlsx", sample_xlsx, XLSX_MEDIA)})
    assert r.status_code == 401


def test_parse_first_sheet(client, auth_headers, sample_xlsx):
    r = client.post(URL, headers=auth_headers, files={"file": ("clientes.xlsx", sample_xlsx, XLSX_MEDIA)})
    assert r.status_code == 200
    body = r.json()
    assert body["bundles"] == [
        {"Nombre": "Ana", "Edad": 30, "Ciudad": "Madrid", "Registro": "2024-01-15T10:30:00"},
        {"Nombre": "Luis", "Edad": 25, "Ciudad": None, "Registro": "2024-02-20T08:00:00"},
    ]
    assert body["meta"] == {
        "sheets": ["Clientes", "Ventas"],
        "sheet": "Clientes",
        "rows": 2,
        "columns": ["Nombre", "Edad", "Ciudad", "Registro"],
    }


def test_parse_raw_binary_body(client, auth_headers, sample_xlsx):
    r = client.post(
        URL,
        headers={**auth_headers, "Content-Type": "application/octet-stream"},
        content=sample_xlsx,
    )
    assert r.status_code == 200
    assert r.json()["meta"]["rows"] == 2


def test_parse_sheet_by_name(client, auth_headers, sample_xlsx):
    r = client.post(URL, headers=auth_headers, params={"sheet": "Ventas"}, files={"file": ("d.xlsx", sample_xlsx, XLSX_MEDIA)})
    assert r.status_code == 200
    assert r.json()["bundles"] == [{"ID": 1, "Total": 100.5}]


def test_parse_sheet_by_index(client, auth_headers, sample_xlsx):
    r = client.post(URL, headers=auth_headers, params={"sheet": "1"}, files={"file": ("d.xlsx", sample_xlsx, XLSX_MEDIA)})
    assert r.status_code == 200
    assert r.json()["meta"]["sheet"] == "Ventas"


def test_sheet_not_found(client, auth_headers, sample_xlsx):
    r = client.post(URL, headers=auth_headers, params={"sheet": "NoExiste"}, files={"file": ("d.xlsx", sample_xlsx, XLSX_MEDIA)})
    assert r.status_code == 404


def test_not_excel_file(client, auth_headers):
    r = client.post(URL, headers=auth_headers, files={"file": ("fake.xlsx", b"esto no es un excel", XLSX_MEDIA)})
    assert r.status_code == 400


def test_unsupported_extension(client, auth_headers, sample_xlsx):
    r = client.post(URL, headers=auth_headers, files={"file": ("datos.csv", sample_xlsx, "text/csv")})
    assert r.status_code == 400


def test_empty_body(client, auth_headers):
    r = client.post(URL, headers={**auth_headers, "Content-Type": "application/octet-stream"}, content=b"")
    assert r.status_code == 400


def test_header_row_param(client, auth_headers, sample_xlsx):
    r = client.post(URL, headers=auth_headers, params={"header_row": 1}, files={"file": ("d.xlsx", sample_xlsx, XLSX_MEDIA)})
    assert r.status_code == 200
    meta = r.json()["meta"]
    assert meta["columns"] == ["Ana", "30", "Madrid", "2024-01-15 10:30:00"]
    assert meta["rows"] == 1


def test_columns_endpoint(client, auth_headers, sample_xlsx):
    r = client.post(COLUMNS_URL, headers=auth_headers, files={"file": ("d.xlsx", sample_xlsx, XLSX_MEDIA)})
    assert r.status_code == 200
    assert r.json() == {
        "columns": ["Nombre", "Edad", "Ciudad", "Registro"],
        "sheets": ["Clientes", "Ventas"],
        "sheet": "Clientes",
    }


def test_verify(client, auth_headers):
    assert client.get("/api/v1/verify", headers=auth_headers).status_code == 200
    assert client.get("/api/v1/verify").status_code == 401


def test_api_key_matches_settings(client, sample_xlsx):
    assert TEST_API_KEY
    r = client.post(URL, headers={AUTH_HEADER: TEST_API_KEY}, files={"file": ("d.xlsx", sample_xlsx, XLSX_MEDIA)})
    assert r.status_code == 200
