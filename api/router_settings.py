"""Endpoint settings & tema (reader layout)."""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

from core.storage import load_json, safe_save_json
import core.config
from models.settings import ReaderSettings

router = APIRouter(prefix="/api", tags=["settings"])

SETTINGS_JSON = getattr(core.config, "SETTINGS_JSON", core.config.BASE_DIR / "reader_settings.json")


def _settings_file() -> Path:
    import api.router_settings as _self
    mod_val = getattr(_self, "SETTINGS_JSON", None)
    if mod_val is not None and mod_val != getattr(core.config, "SETTINGS_JSON", None):
        return Path(mod_val)
    getter = getattr(core.config, "get_settings_path", None)
    if callable(getter):
        return getter()
    return Path(mod_val) if mod_val else core.config.BASE_DIR / "reader_settings.json"
_settings_cache: tuple | None = None


def clear_settings_cache() -> None:
    global _settings_cache
    _settings_cache = None


class SettingsRequest(BaseModel):
    font_size: int | None = None
    line_spacing: float | None = None
    paragraph_indent: int | None = None
    page_margin: int | None = None
    read_width: int | None = None
    theme: str | None = None
    show_original: bool | None = None


@router.get("/settings")
def get_settings():
    global _settings_cache
    s_file = _settings_file()
    path_key = str(s_file)
    try:
        mtime = s_file.stat().st_mtime_ns
    except (FileNotFoundError, OSError):
        mtime = 0

    if _settings_cache is not None and _settings_cache[0] == mtime and _settings_cache[1] == path_key:
        return dict(_settings_cache[2])

    data = load_json(s_file)
    res = ReaderSettings(**data).model_dump()
    _settings_cache = (mtime, path_key, res)
    return res

@router.post("/settings")
def post_settings(req: SettingsRequest):
    s_file = _settings_file()
    cur = load_json(s_file)
    merged = ReaderSettings(**cur)
    for field in ["font_size", "line_spacing", "paragraph_indent", "page_margin", "read_width", "theme", "show_original"]:
        val = getattr(req, field)
        if val is not None:
            setattr(merged, field, val)
    dumped = merged.model_dump()
    safe_save_json(s_file, dumped)
    try:
        mtime = s_file.stat().st_mtime_ns
    except (FileNotFoundError, OSError):
        mtime = 0
    global _settings_cache
    _settings_cache = (mtime, str(s_file), dumped)
    return dumped

@router.post("/theme")
def post_theme(theme: str = "light"):
    if theme not in ("light", "dark"):
        theme = "light"
    s_file = _settings_file()
    cur = load_json(s_file)
    merged = ReaderSettings(**cur)
    merged.theme = theme
    dumped = merged.model_dump()
    safe_save_json(s_file, dumped)
    try:
        mtime = s_file.stat().st_mtime_ns
    except (FileNotFoundError, OSError):
        mtime = 0
    global _settings_cache
    _settings_cache = (mtime, str(s_file), dumped)
    return {"theme": theme}
