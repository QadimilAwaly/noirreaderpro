from pathlib import Path

from services import library as lib


def _make_indexed(root: Path):
    novel_folder = root / "My Novel"
    novel_folder.mkdir()
    (novel_folder / "Chapter_01.md").write_text(
        "# Chapter 1: Awal\n\n---\n\n## Hasil Terjemahan\n\nHalo dunia.\n\n---\n\n## Teks Asli\n\nHello world.\n",
        encoding="utf-8",
    )
    idx = {
        "novels": [{"id": "nov_1", "judul": "My Novel", "folder_path": str(novel_folder)}],
        "chapters": [
            {"id": "c1", "novel_id": "nov_1", "nomor_chapter": 1,
             "judul_chapter": "Awal", "teks_terjemahan": "Halo dunia.", "teks_asli": "Hello world.",
             "status_pengerjaan": "Selesai"}
        ],
    }
    (root / "library_index.json").write_text(__import__("json").dumps(idx), encoding="utf-8")
    return novel_folder


def test_indexed_load(tmp_path: Path):
    root = tmp_path / "lib"
    root.mkdir()
    _make_indexed(root)
    novels = lib.load_library(str(root))
    assert len(novels) == 1
    assert novels[0].judul == "My Novel"
    assert novels[0].chapter_count == 1
    assert novels[0].has_original is True


def test_legacy_txt_md_epub(tmp_path: Path):
    root = tmp_path / "lib"
    root.mkdir()
    novel = root / "Novel A"
    novel.mkdir()
    (novel / "Chapter_01.txt").write_text("Bab satu isi.", encoding="utf-8")
    (novel / "Chapter_02.md").write_text(
        "# Chapter 2\n\n---\n\n## Hasil Terjemahan\n\nDua.\n\n---\n\n## Teks Asli\n\nTwo.\n", encoding="utf-8")
    # buat epub dummy
    import zipfile
    ep = novel / "Book.epub"
    with zipfile.ZipFile(ep, "w") as z:
        z.writestr("META-INF/container.xml",
                   '<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr("content.opf",
                   '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf"><manifest><item id="d1" href="c1.xhtml"/><item id="d2" href="c2.xhtml"/></manifest><spine><itemref idref="d1"/><itemref idref="d2"/></spine></package>')
        z.writestr("c1.xhtml", "<html><head><title>Part Satu</title></head><body><p>Isi satu.</p></body></html>")
        z.writestr("c2.xhtml", "<html><head><title>Part Dua</title></head><body><p>Isi dua.</p></body></html>")
    novels = lib.load_library(str(root))
    assert len(novels) == 1
    chaps = lib.build_chapter_list(str(novel), novel_id=novels[0].id)
    # 2 file (txt, md) + epub 2 parts = 4
    assert len(chaps) == 4
    sources = {c.source for c in chaps}
    assert {"txt", "md", "epub"} <= sources
    epubs = [c for c in chaps if c.source == "epub"]
    assert len(epubs) == 2


def test_natural_sort(tmp_path: Path):
    root = tmp_path / "lib"
    root.mkdir()
    novel = root / "N"
    novel.mkdir()
    for n in [10, 2, 1]:
        (novel / f"Bab_{n}.txt").write_text("x", encoding="utf-8")
    novels = lib.load_library(str(root))
    chaps = lib.build_chapter_list(str(novel), novel_id=novels[0].id)
    titles = [c.title for c in chaps]
    assert titles == ["Bab 1", "Bab 2", "Bab 10"]


def test_multi_root_merging(tmp_path: Path):
    root1 = tmp_path / "Root1"
    root1.mkdir()
    n1 = root1 / "Alpha Novel"
    n1.mkdir()
    (n1 / "Chapter_01.txt").write_text("Bab 1 Alpha.", encoding="utf-8")

    root2 = tmp_path / "Root2"
    root2.mkdir()
    n2 = root2 / "Beta Novel"
    n2.mkdir()
    (n2 / "Chapter_01.txt").write_text("Bab 1 Beta.", encoding="utf-8")

    # Load from multiple roots list
    novels = lib.load_library([str(root1), str(root2)])
    assert len(novels) == 2
    titles = [n.judul for n in novels]
    assert "Alpha Novel" in titles
    assert "Beta Novel" in titles
