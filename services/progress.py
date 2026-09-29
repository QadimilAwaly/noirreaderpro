"""
Progres & bookmark per-novel, disimpan in-folder -> ikut Resilio Sync.

File: <novel_folder>/.<novel_name>_progress.json
Auto-bookmark: tiap chapter yang dibuka otomatis tercatat (tanpa duplikat index).
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from core.storage import load_json, safe_save_json
from models.settings import Bookmark, Progress

_PREFIX = "."

_progress_cache: dict[str, tuple[int, Progress, dict]] = {}


def clear_progress_cache() -> None:
    """Bersihkan cache progres in-memory (untuk testing/reset)."""
    _progress_cache.clear()


def _progress_path(novel_folder: str) -> Path:
    name = Path(novel_folder).name
    safe = re.sub(r"[\\/:*?\"<>|]", "", name).strip() or "novel"
    return Path(novel_folder) / f"{_PREFIX}{safe}_progress.json"


def load_progress(novel_folder: str) -> Progress:
    path = _progress_path(novel_folder)
    path_key = str(path.resolve())
    if not path.exists():
        return Progress()

    try:
        mtime = path.stat().st_mtime_ns
    except OSError:
        mtime = 0

    cached = _progress_cache.get(path_key)
    if cached is not None and cached[0] == mtime:
        c_prog = cached[1]
        return Progress(
            current_chapter_index=c_prog.current_chapter_index,
            bookmarks=list(c_prog.bookmarks),
        )
    data = load_json(path)
    try:
        prog = Progress(
            current_chapter_index=int(data.get("current_chapter_index", 0)),
            bookmarks=[Bookmark(**b) for b in data.get("bookmarks", [])],
        )
        # pastikan urut by chapter_index untuk tampilan
        prog.bookmarks.sort(key=lambda b: b.chapter_index)
        cached_prog = Progress(
            current_chapter_index=prog.current_chapter_index,
            bookmarks=list(prog.bookmarks),
        )
        _progress_cache[path_key] = (mtime, cached_prog, prog.model_dump())
        return prog
    except (ValueError, TypeError):
        return Progress()


def save_progress(novel_folder: str, progress: Progress) -> None:
    progress.bookmarks.sort(key=lambda b: b.chapter_index)
    path = _progress_path(novel_folder)
    path_key = str(path.resolve())
    payload = progress.model_dump()

    cached = _progress_cache.get(path_key)
    if cached is not None and cached[2] == payload and path.exists():
        # Lewati penulisan disk jika data identik (hemat siklus flash & daya baterai)
        return

    safe_save_json(path, payload)
    try:
        mtime = path.stat().st_mtime_ns
    except OSError:
        mtime = 0
    cached_prog = Progress(
        current_chapter_index=progress.current_chapter_index,
        bookmarks=list(progress.bookmarks),
    )
    _progress_cache[path_key] = (mtime, cached_prog, payload)
def add_bookmark_raw(prog: Progress, chapter_index: int, label: str = "") -> Progress:
    bm = Bookmark(
        id=f"bm_{os.urandom(5).hex()}",
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
    return datetime.now(timezone.utc).isoformat()
