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
