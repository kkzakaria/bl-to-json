from datetime import datetime, timezone
from typing import Optional
from fastapi import Header, HTTPException
from app.config import settings
import hmac
import uuid


def verify_api_key(x_api_key: Optional[str] = Header(default=None)) -> str:
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.app_api_key):
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
