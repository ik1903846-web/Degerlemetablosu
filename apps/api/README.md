# REELDEĞER API

FastAPI backend for REELDEĞER Damodaran-aligned BIST valuation system.

## Setup

```bash
source .venv/Scripts/activate
pip install -e ".[dev]"
```

## Run

```bash
uvicorn main:app --reload --port 8000
```

## Endpoints

- `GET /health` → service status
- `GET /docs` → OpenAPI UI
- `GET /redoc` → ReDoc UI
