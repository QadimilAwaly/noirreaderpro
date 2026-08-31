"""
Pengambilan isi chapter dari berbagai sumber:
  - indexed: dari library_index.json chapters[] (terjemahan/asli)
  - md: parse Chapter_NN.md -> pisah "Hasil Terjemahan" vs "Teks Asli"
  - txt: format **tebal**/*miring* -> <p>
  - epub: dari services.epub.get_epub_chapter
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Optional

from models.novel import ChapterContent

# In-memory cache for parsed library_index.json data in reader:
# index_path_resolved -> (mtime_ns, dict[novel_id, list[dict]])
_indexed_reader_cache: dict[str, tuple[int, dict[str, list[dict]]]] = {}


def clear_reader_cache() -> None:
    """Bersihkan cache file library_index.json di reader."""
    _indexed_reader_cache.clear()

def format_plain_markdown(text: str) -> str:
    """Escape HTML, lalu **tebal** / *miring*, lalu tiap baris non-kosong -> <p>."""
    safe = html.escape(text)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"\*(.+?)\*", r"<em>\1</em>", safe)
    out = []
    for line in safe.split("\n"):
        if line.strip():
            out.append(f'<p class="novel-paragraph">{line.strip()}</p>')
    return "\n".join(out)


_MD_DIVIDER = re.compile(r"^---+\s*$", re.MULTILINE)
_MD_TRANS_HEADER = re.compile(r"##\s*Hasil\s*Terjemahan", re.IGNORECASE)
_MD_ORIG_HEADER = re.compile(r"##\s*Teks\s*Asli", re.IGNORECASE)


def _parse_md(content: str) -> tuple[str, Optional[str]]:
    """Kembalikan (translation_html, original_html_or_None) dari markdown translator."""
    # cari posisi header
    trans_m = _MD_TRANS_HEADER.search(content)
    orig_m = _MD_ORIG_HEADER.search(content)
    translation_src = content
    original_src: Optional[str] = None

    if trans_m:
        start = trans_m.end()
        end = orig_m.start() if orig_m and orig_m.start() > start else len(content)
        translation_src = content[start:end]
    if orig_m:
        original_src = content[orig_m.end():]

    translation = format_plain_markdown(translation_src)
    original = format_plain_markdown(original_src) if original_src else None
    return translation, original


def _get_from_indexed(root: str, novel_id: str, chapter_index: int):
    if not root:
        return None
    idx_path = Path(root) / "library_index.json"
    if not idx_path.exists():
        return None
    try:
        mtime = idx_path.stat().st_mtime_ns
    except OSError:
        return None

    cache_key = str(idx_path.resolve())
    cached = _indexed_reader_cache.get(cache_key)

    if cached is not None and cached[0] == mtime:
        by_novel = cached[1]
    else:
        try:
            with idx_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            return None

        if not isinstance(data, dict):
            return None

        by_novel = {}
        for c in data.get("chapters", []):
            nid = c.get("novel_id", "")
            by_novel.setdefault(nid, []).append(c)

        for chaps_list in by_novel.values():
            chaps_list.sort(key=lambda c: (c.get("nomor_chapter", 0)))

        _indexed_reader_cache[cache_key] = (mtime, by_novel)

    chaps = by_novel.get(novel_id)
    if not chaps and "_" in novel_id:
        for nid in by_novel:
            if novel_id.startswith(nid):
                chaps = by_novel[nid]
                break

    if not chaps or chapter_index < 0 or chapter_index >= len(chaps):
        return None

    c = chaps[chapter_index]
    trans = format_plain_markdown(c.get("teks_terjemahan", "") or "")
    orig_raw = (c.get("teks_asli") or "").strip()
    orig = format_plain_markdown(c.get("teks_asli", "")) if orig_raw else None
    return trans, orig, c.get("judul_chapter", f"Chapter {c.get('nomor_chapter', chapter_index+1)}")

def get_chapter_content(
    root: str,
    novel_folder: str,
    novel_id: str,
    chapter: "object",
) -> ChapterContent:
    """
    chapter: ChapterInfo. Mengembalikan ChapterContent (HTML).
    root dipakai untuk mode indexed.
    """
    ref = chapter.ref
    source = chapter.source
    title = chapter.title

    translation = ""
    original: Optional[str] = None

    if source == "indexed":
        res = _get_from_indexed(root, novel_id, chapter.index)
        if res:
            translation, original, title = res
    elif source == "epub":
        from services.epub import get_epub_chapter
        epub_name, _, epub_idx = ref.partition("#")
        epub_path = Path(novel_folder) / epub_name
        translation = get_epub_chapter(str(epub_path), int(epub_idx or 0))
        original = None
    elif source == "md":
        p = Path(novel_folder) / ref
        if p.exists():
            raw = p.read_text(encoding="utf-8", errors="replace")
            translation, original = _parse_md(raw)
    else:  # txt
        p = Path(novel_folder) / ref
        if p.exists():
            raw = p.read_text(encoding="utf-8", errors="replace")
            translation = format_plain_markdown(raw)
            original = None

    return ChapterContent(
        ref=ref,
        title=title,
        translation=translation,
        original=original,
        index=chapter.index,
        total=-1,  # diisi caller
        source=source,
    )
