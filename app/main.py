from __future__ import annotations
import uuid
import time
from datetime import datetime, timezone
from typing import Optional
import httpx
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Request
from app.auth import verify_api_key
from app.config import settings
from app.schemas import BLResponse, Metadata
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


def build_response(extracted: dict, metadata: Metadata, images_count: int) -> BLResponse:
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


async def _extract_from_url(url: str, request_id: str, start_time: float) -> BLResponse:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=30.0, follow_redirects=True)
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
    except HTTPException:
        raise
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
