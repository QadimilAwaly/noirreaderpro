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
    idx_path = Path(root) / "library_index.json"
    if not idx_path.exists():
        return None
    with idx_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    chaps = [c for c in data.get("chapters", []) if c.get("novel_id") == novel_id]
    chaps.sort(key=lambda c: (c.get("nomor_chapter", 0)))
    if chapter_index < 0 or chapter_index >= len(chaps):
        return None
    c = chaps[chapter_index]
    trans = format_plain_markdown(c.get("teks_terjemahan", "") or "")
    orig_raw = (c.get("teks_asli") or "").strip()
    orig = format_plain_markdown(c.get("teks_asli", "")) if orig_raw else None
    # judul chapter dari md jika ada? indexed pakai judul_chapter
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
