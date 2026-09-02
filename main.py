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
from core.config import BASE_DIR, DEFAULT_HOST, DEFAULT_PORT

from api.router_library import router as library_router
from api.router_chapters import router as chapters_router
from api.router_progress import router as progress_router
from api.router_settings import router as settings_router

app = FastAPI(title="Noir Reader Pro", version="1.0.0")


class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        path = request.url.path
        if path.startswith("/api/"):
            # Dynamic API responses must never be cached by browser
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        elif path.startswith("/static/"):
            # Static CSS, JS, images are cacheable by browser with conditional validation
            response.headers["Cache-Control"] = "public, max-age=3600"
        elif path in ("/", "/landing"):
            # Root HTML & Landing are cached with revalidation (ETag/304) so updates are immediate
            response.headers["Cache-Control"] = "no-cache"
        return response


app.add_middleware(CacheControlMiddleware)

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
    uvicorn.run(app, host=DEFAULT_HOST, port=DEFAULT_PORT)
