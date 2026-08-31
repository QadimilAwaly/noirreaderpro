import zipfile
from pathlib import Path

from services import epub


def _make_epub(path: Path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("META-INF/container.xml",
                   '<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr("OEBPS/content.opf",
                   '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf"><manifest><item id="d1" href="c1.xhtml"/><item id="d2" href="c2.xhtml"/></manifest><spine><itemref idref="d1"/><itemref idref="d2"/></spine></package>')
        z.writestr("OEBPS/c1.xhtml", "<html><head><title>Prolog</title></head><body><p>Paragraph <b>satu</b>.</p><p>Dua.</p></body></html>")
        z.writestr("OEBPS/c2.xhtml", "<html><head><title>Epilog</title></head><body><script>bad()</script><p>Epilog isi.</p></body></html>")


def test_list_epub_chapters(tmp_path: Path):
    ep = tmp_path / "book.epub"
    _make_epub(ep)
    titles = epub.list_epub_chapters(str(ep))
    assert titles == ["Prolog", "Epilog"]


def test_get_epub_chapter_strips_tags(tmp_path: Path):
    ep = tmp_path / "book.epub"
    _make_epub(ep)
    html = epub.get_epub_chapter(str(ep), 0)
    assert "<b>" not in html
    assert "Paragraph" in html
    assert "satu" in html


def test_get_epub_chapter_removes_script(tmp_path: Path):
    ep = tmp_path / "book.epub"
    _make_epub(ep)
    html = epub.get_epub_chapter(str(ep), 1)
    assert "bad()" not in html
    assert "Epilog isi." in html


def test_epub_out_of_range(tmp_path: Path):
    ep = tmp_path / "book.epub"
    _make_epub(ep)
    assert "tidak ditemukan" in epub.get_epub_chapter(str(ep), 99)


def test_list_epub_chapters_caching_and_invalidation(tmp_path: Path, monkeypatch):
    epub.clear_epub_cache()
    ep = tmp_path / "cache_book.epub"
    _make_epub(ep)

    # First call parses and caches
    titles1 = epub.list_epub_chapters(str(ep))
    assert titles1 == ["Prolog", "Epilog"]

    # Spy on zipfile.ZipFile to ensure it's not called on second read (cache hit)
    call_count = 0
    orig_zipfile = zipfile.ZipFile

    def spy_zipfile(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return orig_zipfile(*args, **kwargs)

    monkeypatch.setattr(zipfile, "ZipFile", spy_zipfile)

    titles2 = epub.list_epub_chapters(str(ep))
    assert titles2 == ["Prolog", "Epilog"]
    assert call_count == 0  # Cache hit, zero zip decompression!

    # Now modify the epub (add a third chapter)
    import os, time
    with orig_zipfile(ep, "w") as z:
        z.writestr("META-INF/container.xml",
                   '<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr("OEBPS/content.opf",
                   '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf"><manifest><item id="d1" href="c1.xhtml"/><item id="d2" href="c2.xhtml"/><item id="d3" href="c3.xhtml"/></manifest><spine><itemref idref="d1"/><itemref idref="d2"/><itemref idref="d3"/></spine></package>')
        z.writestr("OEBPS/c1.xhtml", "<html><head><title>Prolog</title></head><body><p>1</p></body></html>")
        z.writestr("OEBPS/c2.xhtml", "<html><head><title>Epilog</title></head><body><p>2</p></body></html>")
        z.writestr("OEBPS/c3.xhtml", "<html><head><title>Ekstra</title></head><body><p>3</p></body></html>")
    os.utime(ep, (time.time() + 10, time.time() + 10))
    # Subsequent call invalidates cache based on new mtime and returns updated list
    titles3 = epub.list_epub_chapters(str(ep))
    assert titles3 == ["Prolog", "Epilog", "Ekstra"]
    assert call_count == 1  # Re-parsed exactly once


def test_list_epub_chapters_corrupt_returns_empty(tmp_path: Path):
    epub.clear_epub_cache()
    corrupt = tmp_path / "corrupt.epub"
    corrupt.write_text("This is not a zip file", encoding="utf-8")
    titles = epub.list_epub_chapters(str(corrupt))
    assert titles == []
