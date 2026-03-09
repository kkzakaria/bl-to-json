# BL-to-JSON

Extracts structured data from **Bill of Lading** documents (PDF or image) using the `mistralai/Mistral-Small-3.2-24B-Instruct-2506` model via [DeepInfra](https://deepinfra.com).

## Features

- Accepts **PDF** (multi-page, up to 5 pages) and **images** (JPEG, PNG)
- Two input modes: **file upload** (multipart) or **URL** (JSON body)
- Returns structured JSON with `success / partial / error` status
- Audit metadata per request (model, latency, confidence, source)
- X-API-Key authentication with constant-time comparison
- Docker-ready, deployed on Render via GitHub Actions

## Extracted Fields

| Field | Description |
|-------|-------------|
| `bl_number` | Bill of Lading number |
| `bl_type` | Original / Seaway Bill / Express BL / Surrender |
| `carrier` | Shipping company |
| `shipper` | Name + address |
| `consignee` | Name + address |
| `notify_party` | Name + address |
| `port_of_loading` | Port of origin |
| `port_of_discharge` | Destination port |
| `vessel` | Ship name |
| `voyage` | Voyage number |
| `containers` | List with number, type, seal, weight, volume, description |
| `total_weight` | Total weight (value + unit) |
| `total_volume` | Total volume (value + unit) |
| `description_of_goods` | Global cargo description |

## API

### `POST /extract`

**Headers:**
```
X-API-Key: your_api_key
```

**Option A — File upload:**
```bash
curl -X POST https://your-service.onrender.com/extract \
  -H "X-API-Key: your_api_key" \
  -F "file=@bill_of_lading.pdf"
```

**Option B — URL:**
```bash
curl -X POST https://your-service.onrender.com/extract \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/bl.pdf"}'
```

**Response:**
```json
{
  "status": "success",
  "bl_number": "MAEU123456789",
  "bl_type": "Original",
  "carrier": "MAERSK LINE",
  "shipper": { "name": "ACME EXPORTS LTD", "address": "Shanghai, China" },
  "consignee": { "name": "GLOBAL IMPORTS INC", "address": "Rotterdam, NL" },
  "notify_party": { "name": "FREIGHT BROKER SA", "address": "Paris, France" },
  "port_of_loading": "SHANGHAI, CHINA",
  "port_of_discharge": "ROTTERDAM, NETHERLANDS",
  "vessel": "MSC AURORA",
  "voyage": "012W",
  "containers": [
    {
      "number": "MSCU1234567",
      "type": "40HC",
      "seal": "SL-9876",
      "weight": { "value": 24500.0, "unit": "KG" },
      "volume": { "value": 67.5, "unit": "CBM" },
      "description_of_goods": "ELECTRONIC COMPONENTS"
    }
  ],
  "total_weight": { "value": 24500.0, "unit": "KG" },
  "total_volume": { "value": 67.5, "unit": "CBM" },
  "description_of_goods": "ELECTRONIC COMPONENTS",
  "missing_fields": [],
  "pages_processed": 1,
  "metadata": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-03-09T14:32:00Z",
    "processing_time_ms": 3420,
    "model": "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
    "source_type": "upload",
    "source_filename": "bl.pdf",
    "source_url": null,
    "file_size_bytes": 204800,
    "file_type": "pdf",
    "pages_total": 1,
    "confidence": "high"
  }
}
```

### `GET /health`

```bash
curl https://your-service.onrender.com/health
# {"status": "ok"}
```

### Error Codes

| Code | Error | Description |
|------|-------|-------------|
| `401` | `INVALID_API_KEY` | Missing or invalid API key |
| `408` | `TIMEOUT` | URL download timed out |
| `413` | `FILE_TOO_LARGE` | File exceeds size limit |
| `415` | `UNSUPPORTED_FORMAT` | Only PDF, JPEG, PNG accepted |
| `422` | `INVALID_INPUT` | No file or URL provided |
| `502` | `UPSTREAM_ERROR` | DeepInfra API error |

## Local Setup

**1. Clone and install:**
```bash
git clone https://github.com/kkzakaria/bl-to-json.git
cd bl-to-json
pip install -r requirements.txt
```

**2. Configure environment:**
```bash
cp .env.example .env
# Edit .env with your keys
```

```env
DEEPINFRA_API_KEY=your_deepinfra_key
APP_API_KEY=your_secret_key
MAX_FILE_SIZE_MB=20
```

**3. Run:**
```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000` — docs at `http://localhost:8000/docs`

## Docker

```bash
docker compose up --build
```

## Tests

```bash
DEEPINFRA_API_KEY=dummy APP_API_KEY=dummy pytest -v
```

## Deployment (Render)

1. Push to `main` triggers GitHub Actions
2. Tests run → Docker image built and pushed to Docker Hub
3. Render deploy hook triggered automatically

**Required GitHub Secrets:**
- `DOCKER_USERNAME` + `DOCKER_PASSWORD`
- `RENDER_DEPLOY_HOOK_URL`

**Render environment variables:**
- `DEEPINFRA_API_KEY`
- `APP_API_KEY`
- `MAX_FILE_SIZE_MB` (default: 20)

## Extraction Notes

The extraction prompt applies these rules for accuracy:

- **Carrier** — company name only, strips label prefixes ("Carrier:", "Shipped by:", etc.)
- **Vessel vs Voyage** — treated as distinct fields; handles Maersk "VOYAGE / VESSEL NAME" layout correctly
- **Container number** — ISO format only (4 letters + 7 digits, e.g. `MSCU1234567`); trailing suffixes (`/ CN`, `ML-CN`) are removed
- **Description of goods** — cargo description only; boilerplate clauses ("SHIPPER'S LOAD AND COUNT", "OCEAN FREIGHT PREPAID", "SAID TO CONTAIN", etc.) are ignored
- **Total weight / volume** — uses explicit grand total if present, otherwise computed by summing per-container values
- **Port of discharge** — checks for "Port of Discharge", "POD", "Destination Port", and "Place of Delivery" labels

## Stack

- [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn
- [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF to image conversion
- [Pillow](https://pillow.readthedocs.io/) — image resizing
- [openai](https://github.com/openai/openai-python) SDK — DeepInfra compatible
- [Pydantic v2](https://docs.pydantic.dev/) — schema validation
- `mistralai/Mistral-Small-3.2-24B-Instruct-2506` via [DeepInfra](https://deepinfra.com/mistralai/Mistral-Small-3.2-24B-Instruct-2506) — chosen for best accuracy + speed after benchmarking vs Gemma-3-27B and Qwen3-VL-235B
