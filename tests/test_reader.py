from pathlib import Path

from services import reader as r


def test_format_markdown_escapes_and_bolds():
    out = r.format_plain_markdown("**tebal** dan *miring* & <script>")
    assert "<strong>tebal</strong>" in out
    assert "<em>miring</em>" in out
    assert "&lt;script&gt;" in out  # escaped
    assert "<p" in out


def test_parse_md_split_translation_original(tmp_path: Path):
    p = tmp_path / "c.md"
    p.write_text(
        "# Chapter 1\n\n---\n\n## Hasil Terjemahan\n\nHalo.\n\n---\n\n## Teks Asli\n\nHello.\n",
        encoding="utf-8")
    from services import library as lib
    # buat ChapterInfo sederhana
    from models.novel import ChapterInfo
    ch = ChapterInfo(ref="c.md", novel_id="x", title="Chapter 1", source="md", has_original=True, index=0)
    content = r.get_chapter_content(str(tmp_path), str(tmp_path), "x", ch)
    assert "Halo." in content.translation
    assert "Hello." in (content.original or "")


def test_indexed_chapter_content_and_caching(tmp_path: Path, monkeypatch):
    import json
    import os
    import time
    r.clear_reader_cache()
    idx_file = tmp_path / "library_index.json"
    data = {
        "novels": [{"id": "nov_indexed", "judul": "Novel Indexed"}],
        "chapters": [
            {
                "id": "c1",
                "novel_id": "nov_indexed",
                "nomor_chapter": 1,
                "judul_chapter": "Chapter Satu",
                "teks_terjemahan": "Ini terjemahan bab 1.",
                "teks_asli": "This is original chapter 1.",
            },
            {
                "id": "c2",
                "novel_id": "nov_indexed",
                "nomor_chapter": 2,
                "judul_chapter": "Chapter Dua",
                "teks_terjemahan": "Ini terjemahan bab 2.",
                "teks_asli": "This is original chapter 2.",
            },
        ],
    }
    idx_file.write_text(json.dumps(data), encoding="utf-8")

    from models.novel import ChapterInfo
    ch1 = ChapterInfo(ref="c1", novel_id="nov_indexed", title="Chapter Satu", source="indexed", index=0)
    ch2 = ChapterInfo(ref="c2", novel_id="nov_indexed", title="Chapter Dua", source="indexed", index=1)

    # First chapter read parses JSON and caches
    content1 = r.get_chapter_content(str(tmp_path), str(tmp_path), "nov_indexed", ch1)
    assert "Ini terjemahan bab 1." in content1.translation
    assert "This is original chapter 1." in (content1.original or "")
    assert content1.title == "Chapter Satu"

    # Spy on json.load to verify cache hit across different chapter reads
    json_load_count = 0
    orig_json_load = json.load

    def spy_json_load(*args, **kwargs):
        nonlocal json_load_count
        json_load_count += 1
        return orig_json_load(*args, **kwargs)

    monkeypatch.setattr(json, "load", spy_json_load)

    # Read second chapter in same novel -> cache hit, zero json.load calls!
    content2 = r.get_chapter_content(str(tmp_path), str(tmp_path), "nov_indexed", ch2)
    assert "Ini terjemahan bab 2." in content2.translation
    assert "This is original chapter 2." in (content2.original or "")
    assert json_load_count == 0

    # Modify library_index.json (update text) -> cache is invalidated by mtime_ns
    data["chapters"][0]["teks_terjemahan"] = "Terjemahan baru bab 1."
    idx_file.write_text(json.dumps(data), encoding="utf-8")
    os.utime(idx_file, (time.time() + 10, time.time() + 10))

    content1_updated = r.get_chapter_content(str(tmp_path), str(tmp_path), "nov_indexed", ch1)
    assert "Terjemahan baru bab 1." in content1_updated.translation
    assert json_load_count == 1  # Re-parsed exactly once


def test_indexed_corrupt_or_missing_index(tmp_path: Path):
    r.clear_reader_cache()
    from models.novel import ChapterInfo
    ch = ChapterInfo(ref="c1", novel_id="nov_missing", title="C1", source="indexed", index=0)

    # Missing index returns empty translation gracefully
    content_missing = r.get_chapter_content(str(tmp_path), str(tmp_path), "nov_missing", ch)
    assert content_missing.translation == ""

    # Corrupt index file returns empty translation gracefully without crashing
    idx_file = tmp_path / "library_index.json"
    idx_file.write_text("NOT_JSON_DATA{{{", encoding="utf-8")
    content_corrupt = r.get_chapter_content(str(tmp_path), str(tmp_path), "nov_missing", ch)
    assert content_corrupt.translation == ""


def test_format_h2o_subscripts_and_superscripts():
    # 1. HTML sub/sup (e.g. H2O and CO2 and 10^5)
    out_html = r.format_plain_markdown("Air adalah H<sub>2</sub>O dan gas CO<sub>2</sub>, daya 10<sup>5</sup>.")
    assert "H<sub>2</sub>O" in out_html
    assert "CO<sub>2</sub>" in out_html
    assert "10<sup>5</sup>" in out_html

    # 2. Markdown sub/sup (~2~ and ^2^)
    out_md = r.format_plain_markdown("Rumus H~2~O dan x^2^ + y^3^ = z serta E = mc^2^.")
    assert "H<sub>2</sub>O" in out_md
    assert "x<sup>2</sup>" in out_md
    assert "mc<sup>2</sup>" in out_md

    # 3. Unicode subscripts and superscripts preserved intact
    out_uni = r.format_plain_markdown("Formula: H₂O + CO₂ → H₂CO₃; x² + y³ = z⁴; ±5°C; ½ porsi.")
    assert "H₂O" in out_uni
    assert "CO₂" in out_uni
    assert "H₂CO₃" in out_uni
    assert "x² + y³ = z⁴" in out_uni
    assert "±5°C" in out_uni
    assert "½ porsi" in out_uni


def test_format_html_entities_and_safe_tags():
    # Entities unescape properly without double-escaping
    out_entities = r.format_plain_markdown("&ldquo;Halo&rdquo; &mdash; tes&hellip; &nbsp; &deg;C")
    assert "“Halo”" in out_entities
    assert "—" in out_entities
    assert "…" in out_entities
    assert "°C" in out_entities

    # Inline formatting: strikethrough, underline, highlight, ruby, code
    out_fmt = r.format_plain_markdown("Teks <u>garis bawah</u>, ~~dicoret~~, ==stabilo==, |東雲《しののめ》, `stats: 100`.")
    assert "<u>garis bawah</u>" in out_fmt
    assert "<del>dicoret</del>" in out_fmt
    assert "<mark>stabilo</mark>" in out_fmt
    assert "<ruby>東雲<rt>しののめ</rt></ruby>" in out_fmt
    assert "<code>stats: 100</code>" in out_fmt

    # Unsafe tags like script or onerror are neutralized
    out_xss = r.format_plain_markdown("<script>alert(1)</script> dan <img src=x onerror=alert(1)>")
    assert "<script>" not in out_xss
    assert "&lt;script&gt;" in out_xss
    assert "&lt;img" in out_xss


def test_read_chapter_file_encoding_fallbacks(tmp_path: Path):
    # 1. UTF-8 with BOM
    f_bom = tmp_path / "bom.txt"
    f_bom.write_bytes("Chapter BOM: H₂O".encode("utf-8-sig"))
    assert "H₂O" in r.read_chapter_file(f_bom)
    assert "\ufeff" not in r.read_chapter_file(f_bom)

    # 2. Windows-1252 / ANSI with em-dash and curly quotes
    f_ansi = tmp_path / "ansi.txt"
    # 0x97 = em-dash —, 0x93/0x94 = curly quotes “ ”, 0xb0 = degree °
    f_ansi.write_bytes(b"Suhu 25\xb0C \x97 air H2O \x93reaksi\x94")
    text_ansi = r.read_chapter_file(f_ansi)
    assert "25°C" in text_ansi
    assert "—" in text_ansi
    assert "“reaksi”" in text_ansi
    assert "\ufffd" not in text_ansi  # No replacement character error!
