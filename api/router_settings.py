"""Endpoint settings & tema (reader layout)."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.storage import load_json, safe_save_json
from core.config import BASE_DIR
from models.settings import ReaderSettings

router = APIRouter(prefix="/api", tags=["settings"])

SETTINGS_JSON = BASE_DIR / "reader_settings.json"


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
    data = load_json(SETTINGS_JSON)
    return ReaderSettings(**data).model_dump()


@router.post("/settings")
def post_settings(req: SettingsRequest):
    cur = load_json(SETTINGS_JSON)
    merged = ReaderSettings(**cur)
    for field in ["font_size", "line_spacing", "paragraph_indent", "page_margin", "read_width", "theme", "show_original"]:
        val = getattr(req, field)
        if val is not None:
            setattr(merged, field, val)
    safe_save_json(SETTINGS_JSON, merged.model_dump())
    return merged.model_dump()


@router.post("/theme")
def post_theme(theme: str = "light"):
    if theme not in ("light", "dark"):
        theme = "light"
    cur = load_json(SETTINGS_JSON)
    merged = ReaderSettings(**cur)
    merged.theme = theme
    safe_save_json(SETTINGS_JSON, merged.model_dump())
    return {"theme": theme}
