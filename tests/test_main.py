# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


MOCK_BL_DATA = {
    "bl_number": "MAEU123",
    "bl_type": "Original",
    "carrier": "MAERSK",
    "shipper": {"name": "ACME", "address": "Shanghai"},
    "consignee": {"name": "GLOBAL", "address": "Rotterdam"},
    "notify_party": {"name": "BROKER", "address": "Paris"},
    "port_of_loading": "SHANGHAI",
    "port_of_discharge": "ROTTERDAM",
    "vessel": "MSC AURORA",
    "voyage": "012W",
    "containers": [],
    "total_weight": {"value": 1000.0, "unit": "KG"},
    "total_volume": {"value": 10.0, "unit": "CBM"},
    "description_of_goods": "ELECTRONICS",
    "confidence": "high",
}


def test_health_endpoint():
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_extract_no_api_key_returns_401():
    from app.main import app
    client = TestClient(app)
    response = client.post("/extract", json={"url": "https://example.com/bl.pdf"})
    assert response.status_code == 401


def test_extract_file_upload_success():
    from app.main import app
    import io
    # Create a minimal JPEG bytes (magic bytes only, enough for detection)
    fake_jpeg = b"\xff\xd8\xff" + b"\x00" * 200

    with patch("app.auth.settings") as mock_auth_settings:
        mock_auth_settings.app_api_key = "testkey"
        with patch("app.main.settings") as mock_settings:
            mock_settings.max_file_size_mb = 20
            with patch("app.main.call_deepinfra", return_value=MOCK_BL_DATA):
                with patch("app.main.prepare_images", return_value=([fake_jpeg], 1)):
                    client = TestClient(app)
                    response = client.post(
                        "/extract",
                        files={"file": ("test.jpg", fake_jpeg, "image/jpeg")},
                        headers={"X-API-Key": "testkey"},
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["bl_number"] == "MAEU123"
                    assert data["status"] in ("success", "partial")
                    assert "metadata" in data


def test_extract_no_file_no_url_returns_422():
    from app.main import app
    with patch("app.auth.settings") as mock_auth_settings:
        mock_auth_settings.app_api_key = "testkey"
        client = TestClient(app)
        # Send multipart with no file field
        response = client.post(
            "/extract",
            data={"dummy": "x"},
            headers={"X-API-Key": "testkey"},
        )
        assert response.status_code in (422, 400)


def test_extract_unsupported_format_returns_415():
    from app.main import app
    with patch("app.auth.settings") as mock_auth_settings:
        mock_auth_settings.app_api_key = "testkey"
        with patch("app.main.settings") as mock_settings:
            mock_settings.max_file_size_mb = 20
            client = TestClient(app)
            response = client.post(
                "/extract",
                files={"file": ("test.docx", b"PK\x03\x04" + b"\x00" * 100, "application/octet-stream")},
                headers={"X-API-Key": "testkey"},
            )
            assert response.status_code == 415
