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
