"""Endpoint library: daftar novel & set library root (mendukung multi-folder)."""
from __future__ import annotations

from pathlib import Path
from typing import List, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.deps import (
    get_library_root,
    get_library_roots,
    get_device_config,
    persist_device_roots,
)
from services import library as lib_service

router = APIRouter(prefix="/api", tags=["library"])


class SetRootRequest(BaseModel):
    path: Union[str, List[str]] | None = None
    paths: List[str] | None = None


@router.get("/state")
def get_state():
    roots: List[str] = []
    try:
        roots = get_library_roots()
    except HTTPException:
        roots = []
    dev = get_device_config()
    return {
        "library_root": roots[0] if roots else "",
        "library_roots": roots,
        "device_library_root": dev.get("library_root", ""),
        "device_library_roots": dev.get("library_roots", []),
    }


@router.get("/novels")
def list_novels():
    roots = get_library_roots()
    novels = lib_service.load_library(roots)
    return {
        "library_roots": roots,
        "library_root": roots[0] if roots else "",
        "novels": [n.model_dump() for n in novels],
    }


@router.post("/set-library-root")
def set_library_root(req: SetRootRequest):
    input_paths = req.paths if req.paths is not None else req.path
    if not input_paths:
        raise HTTPException(status_code=400, detail="Path folder tidak boleh kosong.")

    valid_roots = persist_device_roots(input_paths)
    if not valid_roots:
        raise HTTPException(
            status_code=400,
            detail="Tidak ada folder valid yang ditemukan. Pastikan direktori ada di filesystem.",
        )

    novels = lib_service.load_library(valid_roots)
    return {
        "success": True,
        "library_root": valid_roots[0],
        "library_roots": valid_roots,
        "novel_count": len(novels),
    }
