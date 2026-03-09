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
