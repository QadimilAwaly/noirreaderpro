"""
Deteksi & pembuatan katalog novel dari library root (mendukung multi-folder).

Dua mode per root:
  - indexed: library_index.json ada -> pakai novels[] + chapters[]
  - legacy: scan folder -> .txt/.md/.epub per novel

build_chapter_list(): satukan semua sumber (indexed/txt/md/epub) jadi daftar
terurut natural-sort. EPUB di-expand jadi banyak chapter internal.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Sequence, Union

from models.novel import ChapterInfo, NovelInfo

INDEX_FILENAME = "library_index.json"
_PROGRESS_PREFIX = "."

# In-memory caches for fast library and chapter resolution
_indexed_catalog_cache: dict[str, tuple[int, List[NovelInfo]]] = {}
_legacy_catalog_cache: dict[str, tuple[tuple, List[NovelInfo]]] = {}
_chapter_list_cache: dict[str, tuple[tuple, List[ChapterInfo]]] = {}
_indexed_chapters_cache: dict[tuple[str, str], tuple[int, List[ChapterInfo]]] = {}


def clear_library_cache() -> None:
    """Bersihkan semua cache katalog novel dan daftar chapter."""
    _indexed_catalog_cache.clear()
    _legacy_catalog_cache.clear()
    _chapter_list_cache.clear()
    _indexed_chapters_cache.clear()


# sanitasi nama folder -> id stabil
def _novel_id(folder_path: str) -> str:
    return "nov_" + re.sub(r"[^a-z0-9]+", "_", Path(folder_path).name.lower()).strip("_")


def natural_sort_key(s: str):
    return [float(t) if t.replace(".", "", 1).isdigit() else t.lower()
            for t in re.split(r"([0-9]+(?:\.[0-9]+)?)", s)]


def _try_indexed(root: str) -> List[NovelInfo] | None:
    idx_path = Path(root) / INDEX_FILENAME
    if not idx_path.exists():
        return None
    try:
        mtime = idx_path.stat().st_mtime_ns
    except OSError:
        return None

    root_key = str(Path(root).resolve())
    cached = _indexed_catalog_cache.get(root_key)
    if cached is not None and cached[0] == mtime:
        return [n.model_copy() for n in cached[1]]

    try:
        with idx_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or "novels" not in data:
        return None
    novels_raw = data.get("novels", [])
    chapters_raw = data.get("chapters", [])
    # kelompokkan chapters per novel_id
    by_novel: dict[str, list] = {}
    for c in chapters_raw:
        by_novel.setdefault(c.get("novel_id", ""), []).append(c)

    out: List[NovelInfo] = []
    for n in novels_raw:
        nid = n.get("id") or _novel_id(n.get("folder_path", n.get("judul", "")))
        chaps = by_novel.get(nid, [])
        has_orig = any((c.get("teks_asli") or "").strip() for c in chaps)
        fp = n.get("folder_path", "")
        if fp and not Path(fp).is_absolute():
            fp = str((Path(root) / fp).resolve())
        if not fp:
            fp = str(Path(root) / n.get("judul", "novel"))

        out.append(NovelInfo(
            id=nid,
            judul=n.get("judul", Path(fp).name if fp else "Novel"),
            folder_path=fp,
            chapter_count=len(chaps),
            has_original=bool(has_orig),
        ))
    out.sort(key=lambda x: natural_sort_key(x.judul))
    _indexed_catalog_cache[root_key] = (mtime, out)
    return [n.model_copy() for n in out]


def _scan_legacy(root: str) -> List[NovelInfo]:
    root_path = Path(root)
    try:
        entries = [e for e in root_path.iterdir() if e.is_dir()]
        entries.sort(key=lambda e: natural_sort_key(e.name))
        root_mtime = root_path.stat().st_mtime_ns
        sub_mtimes = tuple((e.name, e.stat().st_mtime_ns) for e in entries)
        sig = (root_mtime, sub_mtimes)
    except OSError:
        return []

    root_key = str(root_path.resolve())
    cached = _legacy_catalog_cache.get(root_key)
    if cached is not None and cached[0] == sig:
        return [n.model_copy() for n in cached[1]]

    out: List[NovelInfo] = []
    for d in entries:
        chaps = build_chapter_list(str(d), novel_id=_novel_id(str(d)), root=root)
        if not chaps:
            continue
        has_orig = any(c.source in ("md", "indexed") for c in chaps)
        out.append(NovelInfo(
            id=_novel_id(str(d)),
            judul=d.name,
            folder_path=str(d),
            chapter_count=len(chaps),
            has_original=has_orig,
        ))
    out.sort(key=lambda x: natural_sort_key(x.judul))
    _legacy_catalog_cache[root_key] = (sig, out)
    return [n.model_copy() for n in out]


def load_library(root_or_roots: Union[str, Sequence[str]]) -> List[NovelInfo]:
    """Muat koleksi novel dari satu atau beberapa folder library root (multi-folder support)."""
    if isinstance(root_or_roots, str):
        roots = [root_or_roots] if root_or_roots else []
    else:
        roots = list(root_or_roots) if root_or_roots else []

    all_novels: List[NovelInfo] = []
    seen_ids: dict[str, str] = {}  # id -> folder_path

    for r in roots:
        if not r or not Path(r).exists():
            continue
        indexed = _try_indexed(r)
        novels_in_root = indexed if indexed is not None else _scan_legacy(r)

        for n in novels_in_root:
            novel_id = n.id
            # Jika ID sudah terpakai oleh folder berbeda, buat ID unik
            if novel_id in seen_ids and seen_ids[novel_id] != n.folder_path:
                suffix = re.sub(r"[^a-z0-9]+", "_", Path(r).name.lower()).strip("_")
                novel_id = f"{n.id}_{suffix}"
                n.id = novel_id

            seen_ids[novel_id] = n.folder_path
            all_novels.append(n)

    all_novels.sort(key=lambda x: natural_sort_key(x.judul))
    return all_novels


def _get_indexed_chapters(root: str, novel_id: str) -> List[ChapterInfo]:
    if not root:
        return []
    idx_path = Path(root) / INDEX_FILENAME
    if not idx_path.exists():
        return []
    try:
        mtime = idx_path.stat().st_mtime_ns
    except OSError:
        return []

    cache_key = (str(Path(root).resolve()), novel_id)
    cached = _indexed_chapters_cache.get(cache_key)
    if cached is not None and cached[0] == mtime:
        return [c.model_copy() for c in cached[1]]

    try:
        with idx_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    target_nid = novel_id
    if "_" in novel_id:
        # Mungkin ada suffix root
        novels_raw = data.get("novels", [])
        for n in novels_raw:
            nid = n.get("id") or ""
            if novel_id.startswith(nid):
                target_nid = nid
                break

    chaps = [c for c in data.get("chapters", []) if c.get("novel_id") == target_nid]
    chaps.sort(key=lambda c: (c.get("nomor_chapter", 0)))
    if not chaps:
        return []

    items: List[ChapterInfo] = []
    for i, c in enumerate(chaps):
        nomor = c.get("nomor_chapter", i + 1)
        judul_raw = c.get("judul_chapter") or f"Chapter {nomor}"
        has_orig = bool((c.get("teks_asli") or "").strip())
        items.append(ChapterInfo(
            ref=c.get("id") or f"chap_{nomor}",
            novel_id=novel_id,
            title=judul_raw,
            source="indexed",
            sort_key=f"chapter_{nomor:04d}",
            has_original=has_orig,
            index=i,
        ))
    _indexed_chapters_cache[cache_key] = (mtime, items)
    return [c.model_copy() for c in items]


def build_chapter_list(novel_folder: str, novel_id: str = "", root: str = "") -> List[ChapterInfo]:
    """
    Kumpulkan chapter dari folder novel:
      - indexed: dari library_index.json jika novel terdaftar
      - .txt / .md: tiap file = 1 chapter
      - .epub: 1 file = banyak chapter internal (diberi ref epub#idx)
    Urut natural-sort berdasar nama file / judul.
    """
    # 1. Coba indexed jika root diberikan atau ada di parent
    if root:
        idx_chaps = _get_indexed_chapters(root, novel_id)
        if idx_chaps:
            return idx_chaps

    if novel_folder:
        parent_root = str(Path(novel_folder).parent)
        idx_chaps = _get_indexed_chapters(parent_root, novel_id)
        if idx_chaps:
            return idx_chaps

    folder = Path(novel_folder)
    if not folder.is_dir():
        return []
    nid = novel_id or _novel_id(novel_folder)

    try:
        folder_mtime = folder.stat().st_mtime_ns
        files = sorted(
            [p for p in folder.iterdir()
             if p.suffix.lower() in (".txt", ".md", ".epub") and p.is_file()],
            key=lambda p: natural_sort_key(p.name),
        )
        file_mtimes = tuple((p.name, p.stat().st_mtime_ns) for p in files)
        sig = (folder_mtime, file_mtimes)
    except OSError:
        return []

    cache_key = str(folder.resolve())
    cached = _chapter_list_cache.get(cache_key)
    if cached is not None and cached[0] == sig:
        return [c.model_copy() for c in cached[1]]

    items: List[ChapterInfo] = []
    idx_counter = 0
    for p in files:
        ext = p.suffix.lower()
        if ext == ".epub":
            from services.epub import list_epub_chapters
            try:
                epub_chaps = list_epub_chapters(str(p))
            except Exception:
                epub_chaps = []
            for i, title in enumerate(epub_chaps):
                items.append(ChapterInfo(
                    ref=f"{p.name}#{i}",
                    novel_id=nid,
                    title=title or f"{p.stem} — Part {i+1}",
                    source="epub",
                    sort_key=f"{p.stem}#{i:04d}",
                    has_original=False,
                    index=idx_counter,
                ))
                idx_counter += 1
        else:
            # txt / md
            stem = p.stem
            title = _pretty_title(stem)
            items.append(ChapterInfo(
                ref=p.name,
                novel_id=nid,
                title=title,
                source=ext.lstrip("."),
                sort_key=stem,
                has_original=(ext == ".md"),
                index=idx_counter,
            ))
            idx_counter += 1

    items.sort(key=lambda c: natural_sort_key(c.sort_key))
    for i, c in enumerate(items):
        c.index = i
    _chapter_list_cache[cache_key] = (sig, items)
    return [c.model_copy() for c in items]

def _pretty_title(stem: str) -> str:
    s = re.sub(r"[_\-]+", " ", stem).strip()
    return s
