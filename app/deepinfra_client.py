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
    if not response.choices or not response.choices[0].message.content:
        return {}
    raw = response.choices[0].message.content
    return parse_llm_response(raw)
