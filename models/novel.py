"""Model data novel & chapter (mirip tipe translator, versi Pydantic)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class NovelInfo(BaseModel):
    id: str
    judul: str
    folder_path: str
    chapter_count: int = 0
    has_original: bool = False  # ada teks asli (indexed/.md)
    is_last_read: bool = False


class ChapterInfo(BaseModel):
    # ref unik: untuk epub pakai f"{epub_name}#{idx}"
    ref: str
    novel_id: str
    title: str
    source: str = "txt"  # txt | md | epub | indexed
    sort_key: str = ""   # untuk natural sort di UI
    has_original: bool = False
    index: int = 0       # urutan chapter ke-


class ChapterContent(BaseModel):
    ref: str
    title: str
    translation: str
    original: Optional[str] = None
    index: int = 0
    total: int = 0
    source: str = "txt"
