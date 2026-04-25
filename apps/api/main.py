from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

logger = structlog.get_logger()

app = FastAPI(
    title="REELDEĞER API",
    description="Damodaran-aligned BIST valuation API",
    version="0.1.0",
)

# CORS — frontend (apps/web) localhost:3000 için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health() -> dict[str, str]:
    """Service health check."""
    logger.info("health_check_called")
    return {"status": "ok", "service": "reeldeger-api", "version": "0.1.0"}

@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint — API info."""
    return {
        "service": "REELDEĞER API",
        "docs": "/docs",
        "health": "/health",
    }
