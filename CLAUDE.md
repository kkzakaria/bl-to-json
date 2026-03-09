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

## Deployment
- Docker image: `docker.io/kkzakaria/bl-to-json:latest`
- CI/CD: GitHub Actions → Docker Hub → Render deploy hook
- Required secrets: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `RENDER_DEPLOY_HOOK_URL`
