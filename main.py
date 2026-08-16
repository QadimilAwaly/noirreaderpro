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

import uvicorn
from core.config import BASE_DIR, DEFAULT_HOST, DEFAULT_PORT

from api.router_library import router as library_router
from api.router_chapters import router as chapters_router
from api.router_progress import router as progress_router
from api.router_settings import router as settings_router

app = FastAPI(title="Noir Reader Pro", version="1.0.0")

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
    return FileResponse(str(FRONTEND / "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host=DEFAULT_HOST, port=DEFAULT_PORT)
