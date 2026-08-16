"""
Progres & bookmark per-novel, disimpan in-folder -> ikut Resilio Sync.

File: <novel_folder>/.<novel_name>_progress.json
Auto-bookmark: tiap chapter yang dibuka otomatis tercatat (tanpa duplikat index).
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import List

from core.storage import load_json, safe_save_json
from models.settings import Bookmark, Progress

_PREFIX = "."


def _progress_path(novel_folder: str) -> Path:
    name = Path(novel_folder).name
    safe = re.sub(r"[\\/:*?\"<>|]", "", name).strip() or "novel"
    return Path(novel_folder) / f"{_PREFIX}{safe}_progress.json"


def load_progress(novel_folder: str) -> Progress:
    data = load_json(_progress_path(novel_folder))
    try:
        prog = Progress(
            current_chapter_index=int(data.get("current_chapter_index", 0)),
            bookmarks=[Bookmark(**b) for b in data.get("bookmarks", [])],
        )
        # pastikan urut by chapter_index untuk tampilan
        prog.bookmarks.sort(key=lambda b: b.chapter_index)
        return prog
    except (ValueError, TypeError):
        return Progress()


def save_progress(novel_folder: str, progress: Progress) -> None:
    progress.bookmarks.sort(key=lambda b: b.chapter_index)
    safe_save_json(_progress_path(novel_folder), progress.model_dump())


def add_bookmark_raw(prog: Progress, chapter_index: int, label: str = "") -> Progress:
    bm = Bookmark(
        id=f"bm_{uuid.uuid4().hex[:10]}",
        chapter_index=chapter_index,
        label=label,
        created_at=_now(),
    )
    prog.bookmarks.append(bm)
    return prog


def add_bookmark(novel_folder: str, chapter_index: int, label: str = "") -> Bookmark:
    prog = load_progress(novel_folder)
    prog = add_bookmark_raw(prog, chapter_index, label)
    save_progress(novel_folder, prog)
    return prog.bookmarks[-1]


def remove_bookmark(novel_folder: str, bookmark_id: str) -> bool:
    prog = load_progress(novel_folder)
    before = len(prog.bookmarks)
    prog.bookmarks = [b for b in prog.bookmarks if b.id != bookmark_id]
    if len(prog.bookmarks) != before:
        save_progress(novel_folder, prog)
        return True
    return False


def dedupe_bookmarks(prog: Progress) -> Progress:
    seen = set()
    out = []
    for b in prog.bookmarks:
        if b.chapter_index in seen:
            continue
        seen.add(b.chapter_index)
        out.append(b)
    prog.bookmarks = out
    prog.bookmarks.sort(key=lambda b: b.chapter_index)
    return prog


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
