# tests/test_extractor.py
import pytest
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
