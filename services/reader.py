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
_chapter_content_cache: dict[tuple, tuple[int, ChapterContent]] = {}


def clear_reader_cache() -> None:
    """Bersihkan cache file library_index.json & isi chapter di reader."""
    _indexed_reader_cache.clear()
    _chapter_content_cache.clear()


_ALLOWED_TAG_NAMES = {
    "sub", "sup", "strong", "b", "em", "i", "u", "s", "del", "strike",
    "mark", "small", "ruby", "rt", "rp", "code", "br",
    "span", "div", "var"
}

_TAG_NORMALIZATION = {
    "b": "strong",
    "i": "em",
    "s": "del",
    "strike": "del",
}

_RE_TAG = re.compile(r"<\s*(/)?\s*([a-zA-Z0-9]+)(?:\s+[^>]*)?>")
_RE_BOLD = re.compile(r"\*\*(.+?)\*\*")
_RE_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_RE_STRIKE = re.compile(r"~~(.+?)~~")
_RE_SUB = re.compile(r"(?<!~)\~([a-zA-Z0-9\+\-\=\.,_]+)\~(?!~)")
_RE_SUP = re.compile(r"(?<!\^)\^([a-zA-Z0-9\+\-\=\.,_]+)\^(?!\^)")
_RE_RUBY = re.compile(r"[\|｜]([^\s《\|\n\r]+)《([^》\r\n]+)》")
_RE_MARK = re.compile(r"==(.+?)==")
_RE_CODE = re.compile(r"`([^`\n]+)`")
_RE_PLACEHOLDER = re.compile(r"\x00TAG(\d+)\x00")

_LATEX_SYMBOLS = {
    # Greek lowercase
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ",
    r"\epsilon": "ε", r"\varepsilon": "ε", r"\zeta": "ζ", r"\eta": "η",
    r"\theta": "θ", r"\vartheta": "θ", r"\iota": "ι", r"\kappa": "κ",
    r"\lambda": "λ", r"\mu": "μ", r"\nu": "ν", r"\xi": "ξ",
    r"\pi": "π", r"\varpi": "ϖ", r"\rho": "ρ", r"\varrho": "ϱ",
    r"\sigma": "σ", r"\varsigma": "ς", r"\tau": "τ", r"\upsilon": "υ",
    r"\phi": "φ", r"\varphi": "ϕ", r"\chi": "χ", r"\psi": "ψ",
    r"\omega": "ω",
    # Greek uppercase
    r"\Gamma": "Γ", r"\Delta": "Δ", r"\Theta": "Θ", r"\Lambda": "Λ",
    r"\Xi": "Ξ", r"\Pi": "Π", r"\Sigma": "Σ", r"\Upsilon": "Υ",
    r"\Phi": "Φ", r"\Psi": "Ψ", r"\Omega": "Ω",
    # Math operators & relations
    r"\pm": "±", r"\mp": "∓", r"\times": "×", r"\div": "÷",
    r"\cdot": "·", r"\ast": "∗", r"\star": "⋆", r"\circ": "∘",
    r"\bullet": "•",
    r"\leq": "≤", r"\le": "≤", r"\geq": "≥", r"\ge": "≥",
    r"\neq": "≠", r"\ne": "≠", r"\approx": "≈", r"\sim": "∼",
    r"\equiv": "≡", r"\propto": "∝", r"\ll": "≪", r"\gg": "≫",
    # Arrows & sets
    r"\to": "→", r"\rightarrow": "→", r"\leftarrow": "←",
    r"\Rightarrow": "⇒", r"\Leftarrow": "⇐", r"\Leftrightarrow": "⇔",
    r"\leftrightarrow": "↔",
    r"\forall": "∀", r"\exists": "∃", r"\in": "∈", r"\notin": "∉",
    r"\subset": "⊂", r"\subseteq": "⊆", r"\cup": "∪", r"\cap": "∩",
    r"\nabla": "∇", r"\partial": "∂", r"\infty": "∞",
    # Dots & spacing
    r"\dots": "…", r"\cdots": "…", r"\ldots": "…", r"\vdots": "⋮", r"\ddots": "⋱",
    r"\quad": "  ", r"\qquad": "    ", r"\,": " ", r"\;": " ", r"\!": "",
}

_RE_DISPLAY_MATH = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
_RE_INLINE_MATH = re.compile(r"(?<!\\)\$(?!\s)([^$\n\r]+?)(?<!\s|\$)\$")
_RE_MATH_FRAC = re.compile(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}")
_RE_MATH_SQRT_N = re.compile(r"\\sqrt\s*\[([^\[\]]+)\]\s*\{([^{}]+)\}")
_RE_MATH_SQRT = re.compile(r"\\sqrt\s*\{([^{}]+)\}")
_RE_MATH_TEXT = re.compile(r"\\(?:text|mathrm|mathbf|mathit)\s*\{([^{}]+)\}")
_RE_MATH_SUP_BRACES = re.compile(r"\^\{([^{}]+)\}")
_RE_MATH_SUP_CHAR = re.compile(r"\^([a-zA-Z0-9\+\-\=])")
_RE_MATH_SUB_BRACES = re.compile(r"\_\{([^{}]+)\}")
_RE_MATH_SUB_CHAR = re.compile(r"\_([a-zA-Z0-9\+\-\=])")


def render_latex_math_inner(tex: str) -> str:
    """Konversi ekspresi TeX sederhana ke HTML semantik yang rapi & ringan."""
    s = tex.strip()
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    text_blocks = []
    def _save_text(m):
        idx = len(text_blocks)
        text_blocks.append(f'<span class="math-text">{m.group(1)}</span>')
        return f"\x01TXT{idx}\x01"
    s = _RE_MATH_TEXT.sub(_save_text, s)

    for cmd, sym in sorted(_LATEX_SYMBOLS.items(), key=lambda x: len(x[0]), reverse=True):
        if cmd in s:
            s = s.replace(cmd, sym)

    # Sqrt & Fractions
    s = _RE_MATH_SQRT_N.sub(r'<span class="math-sqrt-wrap"><sup>\1</sup>√<span class="math-sqrt">\2</span></span>', s)
    s = _RE_MATH_SQRT.sub(r'<span class="math-sqrt-wrap">√<span class="math-sqrt">\1</span></span>', s)
    for _ in range(3):
        if r"\frac" not in s:
            break
        s = _RE_MATH_FRAC.sub(r'<span class="math-frac"><span class="math-num">\1</span><span class="math-den">\2</span></span>', s)

    # Superscript & Subscript
    s = _RE_MATH_SUP_BRACES.sub(r"<sup>\1</sup>", s)
    s = _RE_MATH_SUP_CHAR.sub(r"<sup>\1</sup>", s)
    s = _RE_MATH_SUB_BRACES.sub(r"<sub>\1</sub>", s)
    s = _RE_MATH_SUB_CHAR.sub(r"<sub>\1</sub>", s)

    # Clean remaining standalone braces
    s = re.sub(r"\{([^{}]+)\}", r"\1", s)

    # Italicize standalone alphabetic variables outside tags/text
    def _italicize(m):
        c = m.group(0)
        return f"<var>{c}</var>"

    parts = re.split(r"(<[^>]+>|\x01TXT\d+\x01)", s)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"[a-zA-Z]", _italicize, parts[i])
    s = "".join(parts)

    for idx, t_html in enumerate(text_blocks):
        s = s.replace(f"\x01TXT{idx}\x01", t_html)

    return s

def read_chapter_file(p: Path) -> str:
    """Baca isi file teks novel dengan penanganan encoding cerdas (UTF-8, UTF-8-BOM, CP1252/ANSI, UTF-16)."""
    try:
        raw_bytes = p.read_bytes()
    except OSError:
        return ""
    try:
        return raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        return raw_bytes.decode("cp1252")
    except UnicodeDecodeError:
        pass
    if len(raw_bytes) >= 2 and (raw_bytes[:2] in (b"\xff\xfe", b"\xfe\xff")):
        try:
            return raw_bytes.decode("utf-16")
        except UnicodeDecodeError:
            pass
    return raw_bytes.decode("utf-8", errors="replace")


def format_plain_markdown(text: str) -> str:
    """
    Format teks novel ke HTML dengan dukungan aman untuk:
      - Penulisan rumus kimia & matematika: H<sub>2</sub>O, H~2~O, 10<sup>5</sup>, x^2^
      - Simbol & entitas HTML (&mdash;, &hellip;, &ldquo;, &deg;C, dll.)
      - Tag inline aman: <sub>, <sup>, <strong>, <b>, <em>, <i>, <u>, <del>, <s>, <ruby>, <mark>, <code>
      - Markdown format: **tebal**, *miring*, ~~coret~~, ==stabilo==, ~sub~, ^sup^, |kanji《furigana》
      - Karakter spesial unicode & multi-bahasa tetap utuh
      - Menetralisir tag berbahaya (<script>, <img>, <iframe>, dll.)
    """
    if not text:
        return ""

    # 1. Unescape entitas HTML hanya jika ada tanda '&' (mempercepat bab biasa tanpa entitas)
    if "&" in text:
        text = html.unescape(text)

    placeholders = []

    # 2. Parsing LaTeX math: $$...$$ (display) dan $...$ (inline)
    if "$" in text:
        def _display_repl(m):
            inner = m.group(1)
            rendered = render_latex_math_inner(inner)
            idx = len(placeholders)
            placeholders.append(f'<div class="math-display">{rendered}</div>')
            return f"\x00TAG{idx}\x00"

        def _inline_repl(m):
            inner = m.group(1)
            # Hindari false-positive mata uang seperti $100 atau $50.00
            if re.match(r"^\d+(?:,\d+)*(?:\.\d+)?$", inner.strip()):
                return m.group(0)
            rendered = render_latex_math_inner(inner)
            idx = len(placeholders)
            placeholders.append(f'<span class="math-inline">{rendered}</span>')
            return f"\x00TAG{idx}\x00"

        text = _RE_DISPLAY_MATH.sub(_display_repl, text)
        text = _RE_INLINE_MATH.sub(_inline_repl, text)

    # 3. Lindungi tag inline yang aman sebelum escaping (hanya jika ada tanda '<')
    if "<" in text:
        def _save_tag(m):
            slash = m.group(1) or ""
            raw_tag = m.group(2).lower()
            if raw_tag in _ALLOWED_TAG_NAMES:
                tag_name = _TAG_NORMALIZATION.get(raw_tag, raw_tag)
                idx = len(placeholders)
                full_match = m.group(0)
                if raw_tag in ("span", "div", "var"):
                    placeholders.append(full_match)
                elif tag_name == "br":
                    placeholders.append("<br />")
                else:
                    placeholders.append(f"<{slash}{tag_name}>")
                return f"\x00TAG{idx}\x00"
            return m.group(0)
        text = _RE_TAG.sub(_save_tag, text)

    # 4. Escape semua karakter & tag selain yang sudah dilindungi
    safe = html.escape(text)

    # 5. Parsing sintaks Markdown inline (short-circuit: lewati regex jika karakter pemicu tidak ada)
    if "~" in safe:
        safe = _RE_SUB.sub(r"<sub>\1</sub>", safe)
        safe = _RE_STRIKE.sub(r"<del>\1</del>", safe)
    if "^" in safe:
        safe = _RE_SUP.sub(r"<sup>\1</sup>", safe)
    if "==" in safe:
        safe = _RE_MARK.sub(r"<mark>\1</mark>", safe)
    if "`" in safe:
        safe = _RE_CODE.sub(r"<code>\1</code>", safe)
    if "《" in safe:
        safe = _RE_RUBY.sub(r"<ruby>\1<rt>\2</rt></ruby>", safe)
    if "*" in safe:
        safe = _RE_BOLD.sub(r"<strong>\1</strong>", safe)
        safe = _RE_ITALIC.sub(r"<em>\1</em>", safe)

    # 5. Kembalikan tag inline yang dilindungi (single-pass regex replacement)
    if placeholders:
        safe = _RE_PLACEHOLDER.sub(lambda m: placeholders[int(m.group(1))], safe)

    # 6. Susun paragraf
    out = []
    for line in safe.split("\n"):
        s = line.strip()
        if s:
            out.append(f'<p class="novel-paragraph">{s}</p>')
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
    try:
        mtime = idx_path.stat().st_mtime_ns
    except (FileNotFoundError, OSError):
        return None

    cache_key = str(idx_path)
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
    if "_cached_parsed" in c:
        return c["_cached_parsed"]
    raw_trans = c.get("teks_terjemahan", "") or c.get("translation", "") or ""
    trans = format_plain_markdown(raw_trans)
    orig_raw = (c.get("teks_asli") or "").strip()
    orig = format_plain_markdown(orig_raw) if orig_raw else None
    title = c.get("judul_chapter", f"Chapter {c.get('nomor_chapter', chapter_index+1)}")
    parsed = (trans, orig, title)
    c["_cached_parsed"] = parsed
    return parsed

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

    # 1. Cek chapter content cache
    cache_key = None
    mtime = 0
    try:
        if source == "indexed":
            idx_p = Path(root) / "library_index.json"
            mtime = idx_p.stat().st_mtime_ns
            cache_key = ("indexed", str(idx_p), novel_id, chapter.index)
        elif source == "epub":
            epub_name, _, epub_idx = ref.partition("#")
            ep_p = Path(novel_folder) / epub_name
            mtime = ep_p.stat().st_mtime_ns
            cache_key = ("epub", str(ep_p), int(epub_idx or 0))
        else:  # md / txt
            ch_p = Path(novel_folder) / ref
            mtime = ch_p.stat().st_mtime_ns
            cache_key = (source, str(ch_p))
    except (FileNotFoundError, OSError):
        cache_key = None

    if cache_key is not None:
        cached = _chapter_content_cache.get(cache_key)
        if cached is not None and cached[0] == mtime:
            c_obj = cached[1]
            return ChapterContent(
                ref=c_obj.ref,
                title=c_obj.title,
                translation=c_obj.translation,
                original=c_obj.original,
                index=chapter.index,
                total=-1,
                source=c_obj.source,
            )

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
        raw = read_chapter_file(ch_p)
        if raw:
            translation, original = _parse_md(raw)
    else:  # txt
        raw = read_chapter_file(ch_p)
        if raw:
            translation = format_plain_markdown(raw)
        original = None

    content = ChapterContent(
        ref=ref,
        title=title,
        translation=translation,
        original=original,
        index=chapter.index,
        total=-1,  # diisi caller
        source=source,
    )
    if cache_key is not None and mtime > 0:
        _chapter_content_cache[cache_key] = (mtime, content)
    return content
