"""Dependency FastAPI: resolver library root & device config (mendukung multi-folder)."""
from __future__ import annotations

from pathlib import Path
from typing import List, Union

from core.paths import (
    resolve_library_root,
    resolve_library_roots,
    load_device_config,
    save_device_config,
    _extract_paths,
)
from fastapi import HTTPException


def get_library_roots() -> List[str]:
    roots = resolve_library_roots()
    if not roots:
        raise HTTPException(
            status_code=404,
            detail="Library root belum diset. Buka Set Folder (UI) atau isi 'library_roots' di config.json.",
        )
    return roots


def get_library_root() -> str:
    root = resolve_library_root()
    if not root:
        raise HTTPException(
            status_code=404,
            detail="Library root belum diset. Buka Set Folder (UI) atau isi 'library_roots' di config.json.",
        )
    return root


def get_device_config() -> dict:
    return load_device_config()


def persist_device_roots(paths: Union[str, List[str]]) -> List[str]:
    raw_paths = _extract_paths(paths)
    valid_paths: List[str] = []
    for p in raw_paths:
        pp = Path(p)
        if pp.exists() and pp.is_dir():
            resolved = str(pp.resolve())
            if resolved not in valid_paths:
                valid_paths.append(resolved)

    cfg = load_device_config()
    cfg["library_roots"] = valid_paths
    cfg["library_root"] = valid_paths[0] if valid_paths else ""
    save_device_config(cfg)
    return valid_paths


def persist_device_root(library_root: str) -> None:
    persist_device_roots(library_root)
