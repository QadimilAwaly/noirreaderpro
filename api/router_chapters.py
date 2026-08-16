"""Endpoint chapters: daftar & isi chapter (mendukung multi-folder)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional, Tuple, Union

from fastapi import APIRouter, HTTPException, Query

from api.deps import get_library_roots
from services import library as lib_service, reader as reader_service, progress as prog_service
from models.novel import ChapterInfo

router = APIRouter(prefix="/api", tags=["chapters"])


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def find_novel_location(
    roots: Union[str, List[str]], novel_id: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Cari lokasi folder novel di seluruh library_roots.
    Mengembalikan (matched_root, folder_path).
    """
    root_list = [roots] if isinstance(roots, str) else list(roots)

    for root in root_list:
        if not root or not Path(root).exists():
            continue
        root_path = Path(root)
        idx = root_path / "library_index.json"

        # 1. Cek indexed di root ini
        if idx.exists():
            try:
                data = json.loads(idx.read_text(encoding="utf-8"))
                for n in data.get("novels", []):
                    nid = n.get("id") or ("nov_" + _norm(n.get("judul", "")))
                    suffix = _norm(root_path.name)
                    if nid == novel_id or f"{nid}_{suffix}" == novel_id:
                        fp = n.get("folder_path", "")
                        if fp and not Path(fp).is_absolute():
                            fp = str((root_path / fp).resolve())
                        if fp and Path(fp).is_dir():
                            return root, fp

                        # Cari by judul/folder name di root
                        want = _norm(n.get("judul", "") or Path(fp).name)
                        for d in root_path.iterdir():
                            if d.is_dir() and _norm(d.name) == want:
                                return root, str(d)
                        if fp:
                            return root, fp
            except (json.JSONDecodeError, OSError):
                pass

        # 2. Cek scan legacy di root ini
        try:
            for d in root_path.iterdir():
                if d.is_dir():
                    nid = "nov_" + _norm(d.name)
                    suffix = _norm(root_path.name)
                    if nid == novel_id or f"{nid}_{suffix}" == novel_id:
                        return root, str(d)
        except OSError:
            pass

    return None, None


def _find_novel_folder(root: str, novel_id: str) -> str | None:
    _, folder = find_novel_location(root, novel_id)
    return folder


@router.get("/chapters")
def get_chapters(novel_id: str = Query(...)):
    roots = get_library_roots()
    root, folder = find_novel_location(roots, novel_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Novel tidak ditemukan.")

    chapters = lib_service.build_chapter_list(folder, novel_id=novel_id, root=root or "")
    prog = prog_service.load_progress(folder)
    return {
        "novel_id": novel_id,
        "novel_folder": folder,
        "chapters": [c.model_dump() for c in chapters],
        "current_index": prog.current_chapter_index,
        "bookmarks": [b.model_dump() for b in prog.bookmarks],
    }


@router.get("/chapter")
def get_chapter(novel_id: str = Query(...), ref: str = Query(...)):
    roots = get_library_roots()
    root, folder = find_novel_location(roots, novel_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Novel tidak ditemukan.")

    chapters = lib_service.build_chapter_list(folder, novel_id=novel_id, root=root or "")
    target = next((c for c in chapters if c.ref == ref or str(c.index) == ref), None)
    if not target:
        raise HTTPException(status_code=404, detail="Chapter tidak ditemukan.")

    content = reader_service.get_chapter_content(root or "", folder, novel_id, target)
    content.total = len(chapters)

    # auto-save progress
    prog = prog_service.load_progress(folder)
    prog.current_chapter_index = target.index
    prog_service.save_progress(folder, prog)
    return content.model_dump()
