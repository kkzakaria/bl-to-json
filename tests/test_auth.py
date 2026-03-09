# tests/test_auth.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.auth import verify_api_key


def make_app():
    from fastapi import Depends
    app = FastAPI()

    @app.get("/test")
    def test_route(key: str = Depends(verify_api_key)):
        return {"ok": True}

    return app


def test_valid_api_key():
    with patch("app.auth.settings") as mock_settings:
        mock_settings.app_api_key = "secret"
        client = TestClient(make_app())
        response = client.get("/test", headers={"X-API-Key": "secret"})
        assert response.status_code == 200


def test_invalid_api_key():
    with patch("app.auth.settings") as mock_settings:
        mock_settings.app_api_key = "secret"
        client = TestClient(make_app())
        response = client.get("/test", headers={"X-API-Key": "wrong"})
        assert response.status_code == 401
        assert response.json()["detail"]["error"] == "INVALID_API_KEY"


def test_missing_api_key():
    with patch("app.auth.settings") as mock_settings:
        mock_settings.app_api_key = "secret"
        client = TestClient(make_app())
        response = client.get("/test")
        assert response.status_code == 401
