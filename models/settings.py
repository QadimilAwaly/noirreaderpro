"""Model settings, device config, & progress (bookmark per-novel)."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from core.config import (
    DEFAULT_FONT_SIZE,
    DEFAULT_LINE_SPACING,
    DEFAULT_PAGE_MARGIN,
    DEFAULT_PARAGRAPH_INDENT,
    DEFAULT_READ_WIDTH,
    DEFAULT_THEME,
)


class ReaderSettings(BaseModel):
    font_size: int = DEFAULT_FONT_SIZE
    line_spacing: float = DEFAULT_LINE_SPACING
    paragraph_indent: int = DEFAULT_PARAGRAPH_INDENT
    page_margin: int = DEFAULT_PAGE_MARGIN
    read_width: int = DEFAULT_READ_WIDTH
    theme: str = DEFAULT_THEME  # 'light' | 'dark'
    show_original: bool = False


class DeviceConfig(BaseModel):
    library_root: str = ""


class Bookmark(BaseModel):
    id: str
    chapter_index: int
    label: str = ""
    created_at: str = ""


class Progress(BaseModel):
    current_chapter_index: int = 0
    bookmarks: List[Bookmark] = Field(default_factory=list)
