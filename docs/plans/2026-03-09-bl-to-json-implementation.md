# BL-to-JSON Service Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a FastAPI service that extracts structured Bill of Lading data from PDFs and images using gemma-3-27b-it vision model via DeepInfra.

**Architecture:** Vision-only pipeline — PDFs are converted to images via PyMuPDF, images are resized with Pillow, then sent as base64 to DeepInfra's OpenAI-compatible API. FastAPI handles auth (X-API-Key), routing, and Pydantic validation of the structured JSON response.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, PyMuPDF (fitz), Pillow, openai SDK, httpx, pydantic v2, pydantic-settings, pytest, Docker, GitHub Actions → Render.

---

### Task 1: Project scaffold & dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/config.py`

**Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
pymupdf==1.24.10
Pillow==10.4.0
openai==1.51.0
httpx==0.27.2
pydantic==2.9.2
pydantic-settings==2.5.2
python-multipart==0.0.12
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
```

**Step 2: Create .env.example**

```
DEEPINFRA_API_KEY=your_deepinfra_key_here
APP_API_KEY=your_app_api_key_here
MAX_FILE_SIZE_MB=20
```

**Step 3: Create app/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    deepinfra_api_key: str
    app_api_key: str
    max_file_size_mb: int = 20

    model_config = {"env_file": ".env"}


settings = Settings()
```

**Step 4: Create app/__init__.py**

```python
```

**Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 6: Commit**

```bash
git add requirements.txt .env.example app/__init__.py app/config.py
git commit -m "feat: project scaffold and config"
```

---

### Task 2: Pydantic schemas

**Files:**
- Create: `app/schemas.py`
- Create: `tests/__init__.py`
- Create: `tests/test_schemas.py`

**Step 1: Write failing tests**

```python
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
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_schemas.py -v
```
Expected: ImportError — `app.schemas` does not exist.

**Step 3: Create app/schemas.py**

```python
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel


class Party(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None


class Measurement(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None


class ContainerItem(BaseModel):
    number: Optional[str] = None
    type: Optional[str] = None
    seal: Optional[str] = None
    weight: Optional[Measurement] = None
    volume: Optional[Measurement] = None
    description_of_goods: Optional[str] = None


class Metadata(BaseModel):
    request_id: str
    timestamp: str
    processing_time_ms: int
    model: str
    source_type: Literal["upload", "url"]
    source_filename: Optional[str] = None
    source_url: Optional[str] = None
    file_size_bytes: int
    file_type: str
    pages_total: int
    confidence: Literal["high", "medium", "low"]


class BLResponse(BaseModel):
    status: Literal["success", "partial", "error"]
    bl_number: Optional[str] = None
    bl_type: Optional[str] = None
    carrier: Optional[str] = None
    shipper: Optional[Party] = None
    consignee: Optional[Party] = None
    notify_party: Optional[Party] = None
    port_of_loading: Optional[str] = None
    port_of_discharge: Optional[str] = None
    vessel: Optional[str] = None
    voyage: Optional[str] = None
    containers: list[ContainerItem] = []
    total_weight: Optional[Measurement] = None
    total_volume: Optional[Measurement] = None
    description_of_goods: Optional[str] = None
    missing_fields: list[str] = []
    pages_processed: int = 0
    metadata: Metadata


class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: str
    timestamp: str


class URLInput(BaseModel):
    url: str
```

**Step 4: Run tests**

```bash
pytest tests/test_schemas.py -v
```
Expected: 2 PASSED.

**Step 5: Commit**

```bash
git add app/schemas.py tests/__init__.py tests/test_schemas.py
git commit -m "feat: add pydantic schemas for BL response"
```

---

### Task 3: Auth middleware

**Files:**
- Create: `app/auth.py`
- Create: `tests/test_auth.py`

**Step 1: Write failing tests**

```python
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
        assert response.json()["error"] == "INVALID_API_KEY"


def test_missing_api_key():
    with patch("app.auth.settings") as mock_settings:
        mock_settings.app_api_key = "secret"
        client = TestClient(make_app())
        response = client.get("/test")
        assert response.status_code == 401
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_auth.py -v
```
Expected: ImportError.

**Step 3: Create app/auth.py**

```python
from datetime import datetime, timezone
from typing import Optional
from fastapi import Header, HTTPException
from app.config import settings
import uuid


def verify_api_key(x_api_key: Optional[str] = Header(default=None)) -> str:
    if not x_api_key or x_api_key != settings.app_api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "INVALID_API_KEY",
                "message": "The provided API key is invalid or missing.",
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    return x_api_key
```

**Step 4: Run tests**

```bash
pytest tests/test_auth.py -v
```
Expected: 3 PASSED.

**Step 5: Commit**

```bash
git add app/auth.py tests/test_auth.py
git commit -m "feat: add X-API-Key authentication middleware"
```

---

### Task 4: System prompt for BL extraction

**Files:**
- Create: `app/prompts.py`

**Step 1: Create app/prompts.py**

```python
BL_EXTRACTION_PROMPT = """You are an expert in maritime shipping documentation.
Your task is to extract structured data from a Bill of Lading document.

Analyze the provided image(s) carefully and extract ALL visible information.

Return a JSON object with EXACTLY this structure (use null for any field not found):

{
  "bl_number": "string or null",
  "bl_type": "Original | Seaway Bill | Express BL | Surrender | null",
  "carrier": "string or null",
  "shipper": {
    "name": "string or null",
    "address": "string or null"
  },
  "consignee": {
    "name": "string or null",
    "address": "string or null"
  },
  "notify_party": {
    "name": "string or null",
    "address": "string or null"
  },
  "port_of_loading": "string or null",
  "port_of_discharge": "string or null",
  "vessel": "string or null",
  "voyage": "string or null",
  "containers": [
    {
      "number": "string or null",
      "type": "string or null (e.g. 20GP, 40HC, 40GP)",
      "seal": "string or null",
      "weight": {
        "value": number or null,
        "unit": "KG | LBS | null"
      },
      "volume": {
        "value": number or null,
        "unit": "CBM | CFT | null"
      },
      "description_of_goods": "string or null"
    }
  ],
  "total_weight": {
    "value": number or null,
    "unit": "KG | LBS | null"
  },
  "total_volume": {
    "value": number or null,
    "unit": "CBM | CFT | null"
  },
  "description_of_goods": "string or null",
  "confidence": "high | medium | low"
}

Rules:
- Return ONLY the JSON object, no markdown, no explanation.
- confidence = "high" if most fields are found, "medium" if some are missing, "low" if document is unclear or not a BL.
- For containers, extract each container as a separate object in the array.
- If the document is not a Bill of Lading or is unreadable, return all fields as null with confidence "low".
"""
```

**Step 2: Commit**

```bash
git add app/prompts.py
git commit -m "feat: add BL extraction system prompt"
```

---

### Task 5: Vision extractor pipeline

**Files:**
- Create: `app/extractor.py`
- Create: `tests/test_extractor.py`

**Step 1: Write failing tests**

```python
# tests/test_extractor.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.extractor import pdf_to_images, resize_image, build_image_messages


def test_resize_image_no_upscale():
    """Image smaller than 1920px should not be resized."""
    from PIL import Image
    import io
    img = Image.new("RGB", (800, 600), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    result = resize_image(buf.getvalue())
    result_img = Image.open(io.BytesIO(result))
    assert result_img.size == (800, 600)


def test_resize_image_downscales_large():
    """Image wider than 1920px should be resized."""
    from PIL import Image
    import io
    img = Image.new("RGB", (3000, 2000), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    result = resize_image(buf.getvalue())
    result_img = Image.open(io.BytesIO(result))
    assert result_img.width <= 1920


def test_pdf_to_images_returns_list():
    """PDF bytes should return at least one image."""
    import fitz
    import io
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Bill of Lading Test")
    buf = io.BytesIO()
    doc.save(buf)
    pdf_bytes = buf.getvalue()
    images = pdf_to_images(pdf_bytes)
    assert len(images) >= 1
    assert isinstance(images[0], bytes)


def test_pdf_to_images_max_5_pages():
    """PDFs with more than 5 pages should be capped at 5."""
    import fitz
    import io
    doc = fitz.open()
    for _ in range(8):
        page = doc.new_page()
        page.insert_text((100, 100), "Page content")
    buf = io.BytesIO()
    doc.save(buf)
    images = pdf_to_images(buf.getvalue())
    assert len(images) <= 5


def test_build_image_messages():
    """build_image_messages should return list of vision content blocks."""
    import base64
    fake_image = b"fake_image_bytes"
    messages = build_image_messages([fake_image])
    assert len(messages) == 1
    assert messages[0]["type"] == "image_url"
    b64 = base64.b64encode(fake_image).decode()
    assert b64 in messages[0]["image_url"]["url"]
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_extractor.py -v
```
Expected: ImportError.

**Step 3: Create app/extractor.py**

```python
from __future__ import annotations
import base64
import io
from PIL import Image
import fitz  # PyMuPDF


MAX_PAGES = 5
MAX_WIDTH = 1920


def pdf_to_images(pdf_bytes: bytes) -> list[bytes]:
    """Convert PDF bytes to a list of JPEG image bytes (max 5 pages)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page_num in range(min(len(doc), MAX_PAGES)):
        page = doc[page_num]
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        images.append(pix.tobytes("jpeg"))
    doc.close()
    return images


def resize_image(image_bytes: bytes) -> bytes:
    """Resize image to max 1920px width if larger, preserving aspect ratio."""
    img = Image.open(io.BytesIO(image_bytes))
    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        new_size = (MAX_WIDTH, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def build_image_messages(images: list[bytes]) -> list[dict]:
    """Build OpenAI vision content blocks from image bytes list."""
    content = []
    for image_bytes in images:
        b64 = base64.b64encode(image_bytes).decode()
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
        })
    return content


def detect_file_type(content: bytes, filename: str = "") -> str:
    """Detect file type from magic bytes or filename extension."""
    if content[:4] == b"%PDF":
        return "pdf"
    if content[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        return "pdf"
    if ext in ("jpg", "jpeg"):
        return "jpeg"
    if ext == "png":
        return "png"
    return "unknown"


def prepare_images(content: bytes, file_type: str) -> tuple[list[bytes], int]:
    """Convert input bytes to list of image bytes and return (images, total_pages)."""
    if file_type == "pdf":
        import fitz
        doc = fitz.open(stream=content, filetype="pdf")
        total_pages = len(doc)
        doc.close()
        images = pdf_to_images(content)
        return [resize_image(img) for img in images], total_pages
    else:
        return [resize_image(content)], 1
```

**Step 4: Run tests**

```bash
pytest tests/test_extractor.py -v
```
Expected: 5 PASSED.

**Step 5: Commit**

```bash
git add app/extractor.py tests/test_extractor.py
git commit -m "feat: add vision pipeline (PDF to images, resize, base64)"
```

---

### Task 6: DeepInfra API client

**Files:**
- Create: `app/deepinfra_client.py`
- Create: `tests/test_deepinfra_client.py`

**Step 1: Write failing tests**

```python
# tests/test_deepinfra_client.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.deepinfra_client import call_deepinfra, parse_llm_response


def test_parse_llm_response_valid_json():
    raw = '{"bl_number": "MAEU123", "carrier": "MAERSK", "confidence": "high"}'
    result = parse_llm_response(raw)
    assert result["bl_number"] == "MAEU123"
    assert result["confidence"] == "high"


def test_parse_llm_response_with_markdown():
    raw = '```json\n{"bl_number": "MAEU123", "confidence": "medium"}\n```'
    result = parse_llm_response(raw)
    assert result["bl_number"] == "MAEU123"


def test_parse_llm_response_invalid_returns_empty():
    raw = "I cannot read this document."
    result = parse_llm_response(raw)
    assert result == {}
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_deepinfra_client.py -v
```
Expected: ImportError.

**Step 3: Create app/deepinfra_client.py**

```python
from __future__ import annotations
import json
import re
from openai import OpenAI
from app.config import settings
from app.prompts import BL_EXTRACTION_PROMPT


DEEPINFRA_BASE_URL = "https://api.deepinfra.com/v1/openai"
MODEL = "google/gemma-3-27b-it"


def get_client() -> OpenAI:
    return OpenAI(
        api_key=settings.deepinfra_api_key,
        base_url=DEEPINFRA_BASE_URL,
    )


def parse_llm_response(raw: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {}


def call_deepinfra(image_content_blocks: list[dict]) -> dict:
    """Send images to DeepInfra and return parsed JSON extraction."""
    client = get_client()
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": BL_EXTRACTION_PROMPT},
                *image_content_blocks,
            ],
        }
    ]
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=2048,
        temperature=0.1,
    )
    raw = response.choices[0].message.content
    return parse_llm_response(raw)
```

**Step 4: Run tests**

```bash
pytest tests/test_deepinfra_client.py -v
```
Expected: 3 PASSED.

**Step 5: Commit**

```bash
git add app/deepinfra_client.py tests/test_deepinfra_client.py
git commit -m "feat: add DeepInfra API client with JSON parsing"
```

---

### Task 7: Main FastAPI app & /extract endpoint

**Files:**
- Create: `app/main.py`
- Create: `tests/test_main.py`

**Step 1: Write failing tests**

```python
# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io


def make_client():
    with patch("app.config.Settings._settings_build_values", return_value={}):
        pass
    from app.main import app
    return TestClient(app)


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


def test_extract_invalid_input_returns_422():
    from app.main import app
    with patch("app.config.settings") as mock_settings:
        mock_settings.app_api_key = "testkey"
        mock_settings.max_file_size_mb = 20
        client = TestClient(app)
        response = client.post(
            "/extract",
            json={},
            headers={"X-API-Key": "testkey"},
        )
        assert response.status_code == 422


def test_extract_url_success():
    from app.main import app
    with patch("app.config.settings") as mock_settings:
        mock_settings.app_api_key = "testkey"
        mock_settings.max_file_size_mb = 20
        mock_settings.deepinfra_api_key = "deepkey"
        with patch("app.main.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"\xff\xd8\xff" + b"\x00" * 100
            mock_response.headers = {"content-length": "103"}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            with patch("app.main.call_deepinfra", return_value=MOCK_BL_DATA):
                client = TestClient(app)
                response = client.post(
                    "/extract",
                    json={"url": "https://example.com/bl.jpg"},
                    headers={"X-API-Key": "testkey"},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["bl_number"] == "MAEU123"
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_main.py -v
```
Expected: ImportError.

**Step 3: Create app/main.py**

```python
from __future__ import annotations
import uuid
import time
from datetime import datetime, timezone
from typing import Optional
import httpx
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse

from app.auth import verify_api_key
from app.config import settings
from app.schemas import BLResponse, Metadata, URLInput, ErrorResponse
from app.extractor import detect_file_type, prepare_images, build_image_messages
from app.deepinfra_client import call_deepinfra

app = FastAPI(title="BL-to-JSON", version="1.0.0")

SUPPORTED_TYPES = {"pdf", "jpeg", "png"}
ALL_FIELDS = [
    "bl_number", "bl_type", "carrier", "shipper", "consignee",
    "notify_party", "port_of_loading", "port_of_discharge",
    "vessel", "voyage", "containers", "total_weight", "total_volume",
    "description_of_goods",
]


@app.get("/health")
def health():
    return {"status": "ok"}


def build_response(
    extracted: dict,
    metadata: Metadata,
    images_count: int,
) -> BLResponse:
    missing = [f for f in ALL_FIELDS if not extracted.get(f)]
    status = "success" if not missing else "partial"

    return BLResponse(
        status=status,
        bl_number=extracted.get("bl_number"),
        bl_type=extracted.get("bl_type"),
        carrier=extracted.get("carrier"),
        shipper=extracted.get("shipper"),
        consignee=extracted.get("consignee"),
        notify_party=extracted.get("notify_party"),
        port_of_loading=extracted.get("port_of_loading"),
        port_of_discharge=extracted.get("port_of_discharge"),
        vessel=extracted.get("vessel"),
        voyage=extracted.get("voyage"),
        containers=extracted.get("containers", []),
        total_weight=extracted.get("total_weight"),
        total_volume=extracted.get("total_volume"),
        description_of_goods=extracted.get("description_of_goods"),
        missing_fields=missing,
        pages_processed=images_count,
        metadata=metadata,
    )


async def process_document(
    content: bytes,
    filename: str,
    source_type: str,
    source_url: Optional[str],
    request_id: str,
    start_time: float,
) -> BLResponse:
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "FILE_TOO_LARGE",
                "message": f"File exceeds {settings.max_file_size_mb}MB limit.",
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    file_type = detect_file_type(content, filename)
    if file_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=415,
            detail={
                "error": "UNSUPPORTED_FORMAT",
                "message": f"Format '{file_type}' not supported. Use PDF, JPEG, or PNG.",
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    images, total_pages = prepare_images(content, file_type)
    image_blocks = build_image_messages(images)

    try:
        extracted = call_deepinfra(image_blocks)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "UPSTREAM_ERROR",
                "message": f"DeepInfra API error: {str(e)}",
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    elapsed_ms = int((time.time() - start_time) * 1000)
    metadata = Metadata(
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        processing_time_ms=elapsed_ms,
        model="google/gemma-3-27b-it",
        source_type=source_type,
        source_filename=filename if source_type == "upload" else None,
        source_url=source_url,
        file_size_bytes=len(content),
        file_type=file_type,
        pages_total=total_pages,
        confidence=extracted.get("confidence", "low"),
    )

    return build_response(extracted, metadata, len(images))


@app.post("/extract", response_model=BLResponse)
async def extract(
    file: Optional[UploadFile] = File(default=None),
    url: Optional[str] = Form(default=None),
    _: str = Depends(verify_api_key),
):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    if file is not None:
        content = await file.read()
        return await process_document(
            content, file.filename or "upload", "upload", None, request_id, start_time
        )

    if url is not None:
        try:
            resp = httpx.get(url, timeout=30.0, follow_redirects=True)
            resp.raise_for_status()
            content = resp.content
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=408,
                detail={
                    "error": "TIMEOUT",
                    "message": "URL download timed out after 30s.",
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "INVALID_INPUT",
                    "message": f"Could not download URL: {str(e)}",
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        filename = url.rsplit("/", 1)[-1] or "document"
        return await process_document(
            content, filename, "url", url, request_id, start_time
        )

    raise HTTPException(
        status_code=422,
        detail={
            "error": "INVALID_INPUT",
            "message": "Provide either a 'file' (multipart) or 'url' (form field).",
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
```

**Note on /extract dual input:** The endpoint accepts both multipart `file` upload and a form `url` field in the same POST. For JSON body with URL, see Task 8.

**Step 4: Run tests**

```bash
pytest tests/test_main.py -v
```
Expected: 4 PASSED.

**Step 5: Run all tests**

```bash
pytest -v
```
Expected: All PASSED.

**Step 6: Commit**

```bash
git add app/main.py tests/test_main.py
git commit -m "feat: add FastAPI app with /extract and /health endpoints"
```

---

### Task 8: Support JSON body URL input

The `/extract` endpoint currently only accepts form data. Add support for `application/json` body with `{"url": "..."}`.

**Files:**
- Modify: `app/main.py`

**Step 1: Update the /extract endpoint to handle both content types**

Replace the existing `/extract` route in `app/main.py`:

```python
from fastapi import Request

@app.post("/extract", response_model=BLResponse)
async def extract(
    request: Request,
    _: str = Depends(verify_api_key),
):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        url = form.get("url")
        if file is not None:
            content = await file.read()
            return await process_document(
                content, file.filename or "upload", "upload", None, request_id, start_time
            )
        if url:
            return await _extract_from_url(str(url), request_id, start_time)

    elif "application/json" in content_type:
        body = await request.json()
        url = body.get("url")
        if url:
            return await _extract_from_url(str(url), request_id, start_time)

    raise HTTPException(
        status_code=422,
        detail={
            "error": "INVALID_INPUT",
            "message": "Provide either a 'file' (multipart) or 'url' (JSON or form).",
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def _extract_from_url(url: str, request_id: str, start_time: float) -> BLResponse:
    try:
        resp = httpx.get(url, timeout=30.0, follow_redirects=True)
        resp.raise_for_status()
        content = resp.content
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=408,
            detail={
                "error": "TIMEOUT",
                "message": "URL download timed out after 30s.",
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_INPUT",
                "message": f"Could not download URL: {str(e)}",
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    filename = url.rsplit("/", 1)[-1] or "document"
    return await process_document(content, filename, "url", url, request_id, start_time)
```

**Step 2: Run all tests**

```bash
pytest -v
```
Expected: All PASSED.

**Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat: support JSON body URL input on /extract"
```

---

### Task 9: Dockerfile & docker-compose

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

**Step 1: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps for PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Create docker-compose.yml**

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

**Step 3: Create .dockerignore**

```
.git
.env
__pycache__
*.pyc
tests/
docs/
.github/
*.md
```

**Step 4: Build and test locally**

```bash
cp .env.example .env
# Fill in DEEPINFRA_API_KEY and APP_API_KEY in .env
docker compose up --build
```

Expected: Server starts on http://localhost:8000, `GET /health` returns `{"status": "ok"}`.

**Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore
git commit -m "feat: add Dockerfile and docker-compose"
```

---

### Task 10: GitHub Actions CI/CD → Render

**Files:**
- Create: `.github/workflows/deploy.yml`

**Prerequisites:**
- GitHub repository created and code pushed
- Docker Hub account (or use GHCR)
- Render Web Service created with external Docker image
- GitHub Secrets set:
  - `DOCKER_USERNAME`
  - `DOCKER_PASSWORD`
  - `RENDER_DEPLOY_HOOK_URL` (from Render dashboard → Settings → Deploy Hook)

**Step 1: Create .github/workflows/deploy.yml**

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest -v
        env:
          DEEPINFRA_API_KEY: dummy_key_for_tests
          APP_API_KEY: dummy_app_key

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ secrets.DOCKER_USERNAME }}/bl-to-json:latest

      - name: Trigger Render deploy
        run: curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}"
```

**Step 2: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "feat: add GitHub Actions CI/CD pipeline for Render deployment"
```

---

### Task 11: Render setup guide

**Render Web Service configuration:**

1. Go to https://render.com → New → Web Service
2. Select "Deploy an existing image from a registry"
3. Image URL: `docker.io/<your-dockerhub-username>/bl-to-json:latest`
4. Instance type: **Starter** (or higher for production)
5. Set environment variables:
   - `DEEPINFRA_API_KEY` = your key
   - `APP_API_KEY` = your secret key
   - `MAX_FILE_SIZE_MB` = 20
6. Copy the **Deploy Hook URL** → add to GitHub Secrets as `RENDER_DEPLOY_HOOK_URL`

**Step 1: Verify end-to-end**

```bash
# Replace with your Render URL
curl -X GET https://your-service.onrender.com/health
# Expected: {"status": "ok"}

curl -X POST https://your-service.onrender.com/extract \
  -H "X-API-Key: your_app_key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/sample-bl.pdf"}'
```

---

### Final: Save memory

**Step 1: Create memory file**

```bash
mkdir -p /home/superz/.claude/projects/-home-superz-bl-to-json/memory/
```

Write `MEMORY.md` with key project facts (stack, model, endpoints, env vars).

---

## Summary

| Task | Component | Status |
|------|-----------|--------|
| 1 | Scaffold & config | - |
| 2 | Pydantic schemas | - |
| 3 | Auth middleware | - |
| 4 | System prompt | - |
| 5 | Vision extractor | - |
| 6 | DeepInfra client | - |
| 7 | FastAPI app | - |
| 8 | JSON URL input | - |
| 9 | Docker | - |
| 10 | GitHub Actions CI/CD | - |
| 11 | Render deployment | - |
