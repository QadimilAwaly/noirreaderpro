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
