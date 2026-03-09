BL_EXTRACTION_PROMPT = """You are an expert in maritime shipping documentation. Extract structured data from the Bill of Lading document image(s) provided.

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
      "type": "string or null",
      "seal": "string or null",
      "weight": { "value": number or null, "unit": "KG | KGS | MT | LBS | null" },
      "volume": { "value": number or null, "unit": "CBM | CFT | null" },
      "description_of_goods": "string or null"
    }
  ],
  "total_weight": { "value": number or null, "unit": "KG | KGS | MT | LBS | null" },
  "total_volume": { "value": number or null, "unit": "CBM | CFT | null" },
  "description_of_goods": "string or null",
  "confidence": "high | medium | low"
}

## Extraction Rules

**carrier**: Extract only the company name. Remove label prefixes like "Carrier:", "Shipped by:", etc.

**vessel & voyage**: These are two distinct fields.
- `vessel` = the ship name (e.g. "MAERSK EDIRNE", "MSC AURORA", "KOTA SYDNEY")
- `voyage` = the voyage/trip number (e.g. "450W", "044W", "0102W") — typically alphanumeric, often ends in W or E
- On some layouts (e.g. Maersk) the format is "VOYAGE / VESSEL NAME" — read carefully.

**container number**: Extract only the ISO container number (4 letters + 7 digits, e.g. "MSCU1234567"). Remove any trailing suffixes like "/ CN", "ML-CN", booking references, or seal numbers.

**description_of_goods**: Extract the actual cargo description (e.g. "MOTORCYCLES AND PARTS", "SOLAR LAMPS AND BRAKE PADS"). Ignore legal/freight clauses such as "SHIPPER'S LOAD AND COUNT", "OCEAN FREIGHT PREPAID", "SAID TO CONTAIN", "DESTINATION CHARGES COLLECT", or any other standard boilerplate text.

**description_of_goods (per container)**: If multiple containers carry different goods, assign the specific description to each container. If all containers carry the same goods, repeat the description for each.

**total_weight / total_volume**: If a grand total is explicitly stated on the document, use it. If not, compute it by summing the individual container weights/volumes. Do not leave null if the per-container values are available.

**port_of_discharge**: Look for fields labeled "Port of Discharge", "POD", "Destination Port", or "Place of Delivery". Do not leave null if any destination port is visible.

**confidence**:
- "high" = 10+ fields extracted successfully
- "medium" = 5–9 fields extracted
- "low" = fewer than 5 fields, or document is not a Bill of Lading

Return ONLY the JSON object. No markdown, no explanation, no preamble.
"""
