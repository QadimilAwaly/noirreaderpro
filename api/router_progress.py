"""Endpoint progress & auto-bookmark per-novel (mendukung multi-folder)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.deps import get_library_roots
from services import progress as prog_service
from models.settings import Progress
from api.router_chapters import find_novel_location

router = APIRouter(prefix="/api", tags=["progress"])


class ProgressRequest(BaseModel):
    current_chapter_index: int = 0
    bookmarks: list = []


class BookmarkRequest(BaseModel):
    chapter_index: int
    label: str = ""


def _folder_for(novel_id: str) -> str:
    roots = get_library_roots()
    _, folder = find_novel_location(roots, novel_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Novel tidak ditemukan.")
    return folder


@router.get("/progress")
def get_progress(novel_id: str = Query(...)):
    folder = _folder_for(novel_id)
    prog = prog_service.load_progress(folder)
    return prog.model_dump()


@router.post("/progress")
def post_progress(novel_id: str = Query(...), req: ProgressRequest = None):
    folder = _folder_for(novel_id)
    prog = Progress(
        current_chapter_index=req.current_chapter_index if req else 0,
        bookmarks=req.bookmarks if req else [],
    )
    prog_service.save_progress(folder, prog)
    return {"success": True}


@router.post("/mark-read")
def mark_read(novel_id: str = Query(...), req: BookmarkRequest = None):
    """Auto-bookmark: catat chapter yang dibuka sebagai bookmark (tanpa duplikat)."""
    folder = _folder_for(novel_id)
    if not req:
        raise HTTPException(status_code=400, detail="Body kosong.")
    prog = prog_service.load_progress(folder)
    prog.current_chapter_index = req.chapter_index

    # auto-tambah bookmark kalau chapter ini belum ada
    exists = any(b.chapter_index == req.chapter_index for b in prog.bookmarks)
    if not exists:
        from services.progress import add_bookmark_raw
        prog = add_bookmark_raw(prog, req.chapter_index, req.label or "")
    else:
        # update label kalau diberi
        if req.label:
            for b in prog.bookmarks:
                if b.chapter_index == req.chapter_index and not b.label:
                    b.label = req.label
    prog_service.save_progress(folder, prog)
    return prog.model_dump()


@router.delete("/bookmark")
def delete_bookmark(novel_id: str = Query(...), bookmark_id: str = Query(...)):
    folder = _folder_for(novel_id)
    ok = prog_service.remove_bookmark(folder, bookmark_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Bookmark tidak ditemukan.")
    return {"success": True}
