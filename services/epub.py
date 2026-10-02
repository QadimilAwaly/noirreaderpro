"""
Parser EPUB minimal via stdlib (zipfile + xml + html.parser).

Tidak butuh lxml/ebooklib -> aman Termux.
Mengikuti standar: cari .opf (content.opf) -> spine -> urutan doc xhtml -> ekstrak teks.
"""
from __future__ import annotations

import os
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

_OPF_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "opf": "http://www.idpf.org/2007/opf",
}

# In-memory cache for parsed EPUB chapter titles: path -> (mtime_ns, titles_list)
_epub_chapters_cache: dict[str, tuple[int, list[str]]] = {}
_epub_spine_cache: dict[str, tuple[int, list[str]]] = {}

def clear_epub_cache() -> None:
    """Bersihkan cache chapter list EPUB (berguna untuk testing / reset)."""
    _epub_chapters_cache.clear()
    _epub_spine_cache.clear()
_EPUB_ALLOWED_INLINE = {
    "sub", "sup", "b", "strong", "i", "em", "u", "s", "del", "mark",
    "small", "ruby", "rt", "rp", "code"
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in ("script", "style"):
            self._skip = True
        elif t in ("p", "div", "br", "h1", "h2", "h3", "h4", "li", "tr", "section", "article"):
            self._parts.append("\n")
        elif t in _EPUB_ALLOWED_INLINE and not self._skip:
            self._parts.append(f"<{t}>")

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("script", "style"):
            self._skip = False
        elif t in ("p", "div", "h1", "h2", "h3", "h4", "li", "tr", "section", "article"):
            self._parts.append("\n")
        elif t in _EPUB_ALLOWED_INLINE and not self._skip:
            self._parts.append(f"</{t}>")

    def handle_data(self, data):
        if not self._skip:
            self._parts.append(data)

    def text(self) -> str:
        raw = "".join(self._parts)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def _strip_html_to_paragraphs(html_text: str) -> str:
    """Format isi bab EPUB ke <p class='novel-paragraph'> dengan tetap mempertahankan inline formatting (sub, sup, dll)."""
    ex = _TextExtractor()
    ex.feed(html_text)
    text = ex.text()
    from services.reader import format_plain_markdown
    return format_plain_markdown(text)

def _find_opf(zf: zipfile.ZipFile) -> str | None:
    # 1. container.xml
    try:
        with zf.open("META-INF/container.xml") as f:
            root = ET.fromstring(f.read())
        for rf in root.iter("{http://www.idpf.org/2007/opf}rootfile"):
            full = rf.get("full-path")
            if full:
                return full
    except (KeyError, ET.ParseError):
        pass
    # 2. fallback cari *.opf
    for name in zf.namelist():
        if name.lower().endswith(".opf"):
            return name
    return None


def _spine_order(zf: zipfile.ZipFile, opf_path: str) -> list[str]:
    """Kembalikan list path doc (xhtml) berurutan spine."""
    try:
        with zf.open(opf_path) as f:
            root = ET.fromstring(f.read())
    except (KeyError, ET.ParseError):
        return []

    # manifest: id -> href
    manifest: dict[str, str] = {}
    man = root.find("opf:manifest", _OPF_NS)
    if man is None:
        man = root.find("manifest")
    if man is not None:
        for item in man:
            _id = item.get("id")
            href = item.get("href")
            if _id and href:
                manifest[_id] = href

    # spine: idref berurutan
    order_ids: list[str] = []
    sp = root.find("opf:spine", _OPF_NS)
    if sp is None:
        sp = root.find("spine")
    if sp is not None:
        for it in sp:
            idref = it.get("idref")
            if idref:
                order_ids.append(idref)

    base = Path(opf_path).parent
    ordered: list[str] = []
    for _id in order_ids:
        href = manifest.get(_id)
        if href:
            ordered.append(str((base / href).as_posix()))
    # fallback: semua xhtml di manifest
    if not ordered:
        for href in manifest.values():
            if href.lower().endswith((".xhtml", ".html", ".htm")):
                ordered.append(str((base / href).as_posix()))
    # filter cuma yang ada di zip & berupa teks
    result = [p for p in ordered if p in zf.namelist()]
    return result


def _doc_title(zf: zipfile.ZipFile, doc_path: str) -> str | None:
    try:
        with zf.open(doc_path) as f:
            data = f.read().decode("utf-8", errors="replace")
    except KeyError:
        return None
    m = re.search(r"<title[^>]*>(.*?)</title>", data, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    # heading pertama
    m2 = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", data, re.IGNORECASE | re.DOTALL)
    if m2:
        return re.sub(r"<[^>]+>", "", m2.group(1)).strip()
    return None


def list_epub_chapters(epub_path: str) -> list[str]:
    """Kembalikan daftar judul chapter (untuk daftar di sidebar), di-cache berdasarkan mtime file."""
    try:
        p = Path(epub_path)
        mtime = p.stat().st_mtime_ns
    except OSError:
        return []

    cache_key = str(p)
    cached = _epub_chapters_cache.get(cache_key)
    if cached is not None and cached[0] == mtime:
        return list(cached[1])

    titles: list[str] = []
    try:
        with zipfile.ZipFile(str(p)) as zf:
            opf = _find_opf(zf)
            if opf:
                docs = _spine_order(zf, opf)
                for i, doc in enumerate(docs):
                    t = _doc_title(zf, doc)
                    titles.append(t or f"Part {i+1}")
    except Exception:
        titles = []

    _epub_chapters_cache[cache_key] = (mtime, titles)
    return list(titles)

def get_epub_chapter(epub_path: str, index: int) -> str:
    """Kembalikan HTML <p> chapter ke-index (1 file epub = banyak chapter)."""
    try:
        mtime = os.stat(epub_path).st_mtime_ns
    except OSError:
        mtime = 0

    cached_spine = _epub_spine_cache.get(epub_path)
    with zipfile.ZipFile(epub_path) as zf:
        if cached_spine is not None and cached_spine[0] == mtime:
            docs = cached_spine[1]
        else:
            opf = _find_opf(zf)
            if not opf:
                return '<p class="novel-paragraph">(EPUB rusak: tidak ada OPF)</p>'
            docs = _spine_order(zf, opf)
            _epub_spine_cache[epub_path] = (mtime, docs)

        if index < 0 or index >= len(docs):
            return '<p class="novel-paragraph">(Chapter tidak ditemukan)</p>'
        doc = docs[index]
        try:
            with zf.open(doc) as f:
                data = f.read().decode("utf-8", errors="replace")
        except KeyError:
            return '<p class="novel-paragraph">(Dokumen tidak ada)</p>'
        # buang header/body tag, ambil inner
        m = re.search(r"<body[^>]*>(.*)</body>", data, re.IGNORECASE | re.DOTALL)
        inner = m.group(1) if m else data
        return _strip_html_to_paragraphs(inner)
