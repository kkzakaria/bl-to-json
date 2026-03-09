# BL-to-JSON — Claude Context

## Tests
- Always prefix test commands: `DEEPINFRA_API_KEY=dummy APP_API_KEY=dummy pytest -v`
- pydantic-settings fails at import without env vars set

## Stack Notes
- PyMuPDF wheels bundle MuPDF — no system `libmupdf-dev` needed in Docker
- Use `asyncio.to_thread()` to wrap sync SDK calls (openai client) in async handlers
- Convert PNG RGBA/P/LA → RGB before saving as JPEG (Pillow will error otherwise)

## Security Patterns
- API key comparison: use `hmac.compare_digest()` not `==`

## GitHub CLI
- Branch protection requires `--input -` with JSON heredoc (not `--field` for nested objects)
- Set secrets: `gh secret set KEY --repo owner/repo --body "value"`

## Model
- Active model: `mistralai/Mistral-Small-3.2-24B-Instruct-2506` (changed from gemma-3-27b-it after benchmark)
- Benchmark result: Mistral 3x faster (~8s vs 26s), better accuracy on containers, POD, vessel name
- Model defined in `app/deepinfra_client.py` (MODEL constant) and hardcoded in `app/main.py` metadata

## Prompt
- File: `app/prompts.py` — `BL_EXTRACTION_PROMPT`
- Key extraction rules added: carrier (strip label prefix), vessel vs voyage (distinct fields, Maersk "VOYAGE / VESSEL" layout), container number (ISO format only: 4 letters + 7 digits), description_of_goods (ignore boilerplate like "SHIPPER'S LOAD AND COUNT"), total_weight/volume (compute from containers if no explicit total), port_of_discharge (check POD / Destination Port / Place of Delivery labels)

## Deployment
- Docker image: `docker.io/kkzakaria/bl-to-json:latest`
- CI/CD: GitHub Actions → Docker Hub → Render deploy hook
- Required secrets: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `RENDER_DEPLOY_HOOK_URL`
