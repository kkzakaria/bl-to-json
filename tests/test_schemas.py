# tests/test_schemas.py
from app.schemas import BLResponse, ContainerItem, Party, Measurement, Metadata


def test_bl_response_success():
    data = {
        "status": "success",
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
        "containers": [
            {
                "number": "MSCU1234567",
                "type": "40HC",
                "seal": None,
                "weight": {"value": 24500.0, "unit": "KG"},
                "volume": {"value": 67.5, "unit": "CBM"},
                "description_of_goods": "ELECTRONICS",
            }
        ],
        "total_weight": {"value": 24500.0, "unit": "KG"},
        "total_volume": {"value": 67.5, "unit": "CBM"},
        "description_of_goods": "ELECTRONICS",
        "missing_fields": [],
        "pages_processed": 1,
        "metadata": {
            "request_id": "abc-123",
            "timestamp": "2026-03-09T14:00:00Z",
            "processing_time_ms": 1000,
            "model": "google/gemma-3-27b-it",
            "source_type": "upload",
            "source_filename": "bl.pdf",
            "source_url": None,
            "file_size_bytes": 1024,
            "file_type": "pdf",
            "pages_total": 1,
            "confidence": "high",
        },
    }
    response = BLResponse(**data)
    assert response.status == "success"
    assert response.bl_number == "MAEU123"
    assert len(response.containers) == 1


def test_bl_response_partial_allows_null_fields():
    data = {
        "status": "partial",
        "bl_number": None,
        "bl_type": None,
        "carrier": None,
        "shipper": None,
        "consignee": None,
        "notify_party": None,
        "port_of_loading": None,
        "port_of_discharge": None,
        "vessel": None,
        "voyage": None,
        "containers": [],
        "total_weight": None,
        "total_volume": None,
        "description_of_goods": None,
        "missing_fields": ["bl_number", "carrier"],
        "pages_processed": 1,
        "metadata": {
            "request_id": "abc-123",
            "timestamp": "2026-03-09T14:00:00Z",
            "processing_time_ms": 500,
            "model": "google/gemma-3-27b-it",
            "source_type": "upload",
            "source_filename": "bad.jpg",
            "source_url": None,
            "file_size_bytes": 512,
            "file_type": "jpeg",
            "pages_total": 1,
            "confidence": "low",
        },
    }
    response = BLResponse(**data)
    assert response.status == "partial"
    assert "bl_number" in response.missing_fields
