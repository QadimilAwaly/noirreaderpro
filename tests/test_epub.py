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
