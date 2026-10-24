"""
Deep-Tech Sprint API - backend core + MCP surface.
FastAPI + MCP (Streamable HTTP) + static UI mount + ops endpoints.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import RedirectResponse

from mcp_bridge import mcp_http_asgi, mcp_http_lifespan

import uvicorn

app = FastAPI(
    title="Deep-Tech Sprint - Autonomous R&D System",
    description="Autonomous R&D pipeline - FastAPI backend core + MCP tools.",
    version="0.1.0",
    lifespan=mcp_http_lifespan,
)

_cors_origins = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
]
for _part in os.getenv("CORS_ALLOW_ORIGINS", "").split(","):
    _o = _part.strip()
    if _o and _o not in _cors_origins:
        _cors_origins.append(_o)

_cors_kw: dict[str, object] = {
    "allow_origins": _cors_origins,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
_cors_rx = os.getenv("CORS_ALLOW_ORIGIN_REGEX", "").strip()
if _cors_rx:
    _cors_kw["allow_origin_regex"] = _cors_rx
app.add_middleware(CORSMiddleware, **_cors_kw)


@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/api")
async def api_info():
    """JSON service info."""
    return {
        "service": "Deep-Tech Sprint API",
        "docs": "/docs",
        "pipeline": "POST /trigger-pipeline",
        "health": "/health",
        "mcp": "/mcp/",
    }


# MCP over HTTP (Streamable HTTP) — mount before catch-all static files
app.mount("/mcp", mcp_http_asgi)


@app.get("/mcp")
async def redirect_to_mcp():
    return RedirectResponse(url="/mcp/", status_code=307)


_FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


@app.get("/", include_in_schema=False)
async def index():
    """Serve the web dashboard when `frontend/` exists, else redirect to /api."""
    if _FRONTEND_DIR.is_dir():
        return RedirectResponse(url="/frontend/", status_code=307)
    return RedirectResponse(url="/api", status_code=307)


if _FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
else:

    @app.get("/", include_in_schema=False)
    async def index_redirect():
        return RedirectResponse(url="/api", status_code=307)


if __name__ == "__main__":
    _port = int(os.environ.get("PORT", "8000"))
    _host = os.environ.get("HOST", "0.0.0.0")
    _url = f"http://127.0.0.1:{_port}"
    print(f"Starting {_url}")
    print(f"Docs: {_url}/docs")
    if _FRONTEND_DIR.is_dir():
        print(f"UI: {_url}/ (same origin as API)")
    print(f"MCP: {_url}/mcp/")
    uvicorn.run(app, host=_host, port=_port)
