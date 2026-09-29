"""
Noir Reader Pro — entry point.

Jalankan:  python main.py
Lalu buka: http://127.0.0.1:3030
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import uvicorn
from core.config import BASE_DIR, DEFAULT_HOST, DEFAULT_PORT, get_host, get_port
from api.router_library import router as library_router
from api.router_chapters import router as chapters_router
from api.router_progress import router as progress_router
from api.router_settings import router as settings_router

app = FastAPI(title="Noir Reader Pro", version="1.0.0")


class CacheControlASGIMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                if path.startswith("/api/"):
                    headers.extend([
                        (b"cache-control", b"no-cache, no-store, must-revalidate"),
                        (b"pragma", b"no-cache"),
                        (b"expires", b"0"),
                    ])
                elif path.startswith("/static/"):
                    headers.append((b"cache-control", b"public, max-age=3600"))
                elif path in ("/", "/landing"):
                    headers.append((b"cache-control", b"no-cache"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


app.add_middleware(CacheControlASGIMiddleware)

# API routers
app.include_router(library_router)
app.include_router(chapters_router)
app.include_router(progress_router)
app.include_router(settings_router)

# Static frontend
FRONTEND = BASE_DIR / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


@app.get("/")
def index():
    return FileResponse(
        str(FRONTEND / "index.html"),
        headers={
            "Cache-Control": "no-cache",
        },
    )

@app.get("/landing")
def landing():
    landing_file = BASE_DIR / "landing.html"
    return FileResponse(
        str(landing_file),
        headers={
            "Cache-Control": "no-cache",
        },
    )


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Noir Reader Pro Server")
    parser.add_argument("--host", default=None, help=f"Host address to bind (default: {get_host()})")
    parser.add_argument("-p", "--port", type=int, default=None, help=f"Port to bind (default: {get_port()})")
    args = parser.parse_args()

    host = args.host or get_host()
    port = args.port or get_port()
    uvicorn.run(app, host=host, port=port)
