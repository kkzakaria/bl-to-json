# tests/test_deepinfra_client.py
from unittest.mock import patch, MagicMock
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


def test_call_deepinfra_calls_api():
    """call_deepinfra should call OpenAI client with correct model and return parsed dict."""
    with patch("app.deepinfra_client.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"bl_number": "TEST123", "confidence": "high"}'
        mock_client.chat.completions.create.return_value = mock_response

        result = call_deepinfra([{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}}])

        assert result["bl_number"] == "TEST123"
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "mistralai/Mistral-Small-3.2-24B-Instruct-2506"
        assert call_kwargs["temperature"] == 0.1
