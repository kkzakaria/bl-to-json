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
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
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
        doc = fitz.open(stream=content, filetype="pdf")
        total_pages = len(doc)
        doc.close()
        images = pdf_to_images(content)
        return [resize_image(img) for img in images], total_pages
    else:
        return [resize_image(content)], 1
