# BL-to-JSON Service — Design Document

**Date:** 2026-03-09
**Status:** Approved

---

## Overview

FastAPI service that extracts structured data from Bill of Lading documents (PDF or image) using the `google/gemma-3-27b-it` multimodal model via DeepInfra's OpenAI-compatible API.

---

## Architecture

```
Client
  │
  ├─ POST /extract  (multipart/form-data: file)
  └─ POST /extract  (application/json: { "url": "..." })
        │
        ▼
   FastAPI App
        │
        ├─ Auth middleware  (X-API-Key)
        ├─ Input handler    (PDF → images[] | image → image)
        ├─ DeepInfra client (OpenAI-compatible SDK)
        └─ Response builder (structured JSON)
        │
        ▼
   DeepInfra API — google/gemma-3-27b-it (vision)
```

**Stack:**
- `fastapi` + `uvicorn`
- `pymupdf` (fitz) — PDF → images conversion
- `Pillow` — image resize/optimization
- `openai` SDK — DeepInfra compatible
- `httpx` — URL file download
- `pydantic` v2 — schema validation
- `pydantic-settings` — env config

**Environment variables:**
```
DEEPINFRA_API_KEY=
APP_API_KEY=
MAX_FILE_SIZE_MB=20
```

---

## Endpoints

```
POST /extract
  Headers: X-API-Key: <key>
  Body (option A): multipart/form-data  { file: <PDF|JPG|PNG> }
  Body (option B): application/json     { "url": "https://..." }

GET /health
  Response: { "status": "ok" }
```

---

## Data Flow

```
1. Auth check (X-API-Key)
2. Input resolution
   ├─ file upload  → read bytes in memory
   └─ URL          → download with httpx (timeout 30s)
3. Type detection (PDF or image)
   ├─ PDF   → PyMuPDF → list of images (1 image/page, max 5 pages)
   └─ image → Pillow  → resize if > 1920px
4. Base64 encoding of each image
5. DeepInfra API call (openai SDK)
   └─ structured prompt + images (vision)
   └─ JSON response format (guided decoding)
6. Pydantic parse & validation
7. Compute missing_fields + status
8. Return JSON
```

**Limits:**
- Max file size: 20 MB (configurable)
- PDFs: first 5 pages only
- DeepInfra timeout: 60s

---

## Output JSON Schema

```json
{
  "status": "success | partial | error",
  "bl_number": "MAEU123456789",
  "bl_type": "Original | Seaway Bill | Express BL | Surrender",
  "carrier": "MAERSK LINE",
  "shipper": {
    "name": "ACME EXPORTS LTD",
    "address": "123 Trade St, Shanghai, China"
  },
  "consignee": {
    "name": "GLOBAL IMPORTS INC",
    "address": "456 Port Ave, Rotterdam, Netherlands"
  },
  "notify_party": {
    "name": "FREIGHT BROKER SA",
    "address": "789 Logistics Blvd, Paris, France"
  },
  "port_of_loading": "SHANGHAI, CHINA",
  "port_of_discharge": "ROTTERDAM, NETHERLANDS",
  "vessel": "MSC AURORA",
  "voyage": "012W",
  "containers": [
    {
      "number": "MSCU1234567",
      "type": "40HC",
      "seal": null,
      "weight": { "value": 24500.0, "unit": "KG" },
      "volume": { "value": 67.5, "unit": "CBM" },
      "description_of_goods": "ELECTRONIC COMPONENTS"
    }
  ],
  "total_weight": { "value": 24500.0, "unit": "KG" },
  "total_volume": { "value": 67.5, "unit": "CBM" },
  "description_of_goods": "ELECTRONIC COMPONENTS",
  "missing_fields": [],
  "pages_processed": 2,
  "metadata": {
    "request_id": "uuid-v4",
    "timestamp": "2026-03-09T14:32:00Z",
    "processing_time_ms": 3420,
    "model": "google/gemma-3-27b-it",
    "source_type": "upload | url",
    "source_filename": "bl_maersk_123.pdf",
    "source_url": null,
    "file_size_bytes": 204800,
    "file_type": "pdf | jpeg | png",
    "pages_total": 3,
    "confidence": "high | medium | low"
  }
}
```

**Status logic:**
- `success` — all fields extracted
- `partial` — one or more fields are null (listed in `missing_fields`)
- `error` — document unreadable / not a BL

---

## Error Handling

| HTTP Code | Error Code | Case |
|-----------|------------|------|
| `401` | `INVALID_API_KEY` | Missing or invalid API key |
| `408` | `TIMEOUT` | DeepInfra timeout > 60s |
| `413` | `FILE_TOO_LARGE` | File > 20 MB |
| `415` | `UNSUPPORTED_FORMAT` | Non PDF/image format |
| `422` | `INVALID_INPUT` | Neither file nor url provided |
| `502` | `UPSTREAM_ERROR` | DeepInfra API error |
| `500` | `INTERNAL_ERROR` | Unexpected internal error |

**Uniform error format:**
```json
{
  "error": "INVALID_API_KEY",
  "message": "The provided API key is invalid or missing.",
  "request_id": "uuid-v4",
  "timestamp": "2026-03-09T14:32:00Z"
}
```

**Special case:** if model cannot read the document → `200` with `status: partial`, all fields `null`, all fields in `missing_fields`.

---

## Project Structure

```
bl-to-json/
├── app/
│   ├── main.py           # FastAPI app, routes
│   ├── auth.py           # X-API-Key middleware
│   ├── extractor.py      # Vision pipeline (PDF→images→DeepInfra)
│   ├── schemas.py        # Pydantic models (input/output)
│   ├── prompts.py        # BL system prompt
│   └── config.py         # Settings (pydantic-settings)
├── tests/
│   ├── test_extract.py
│   └── test_auth.py
├── docs/plans/
├── Dockerfile
├── docker-compose.yml
├── .github/workflows/
│   └── deploy.yml        # Build → push GHCR → deploy Render
├── .env.example
└── requirements.txt
```

---

## CI/CD (GitHub Actions → Render)

```
push to main
  → pytest
  → docker build & push (GHCR)
  → curl Render deploy hook
```

Render configured as **Web Service** with external Docker image from GHCR.
