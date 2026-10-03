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


def test_library_caching_and_invalidation(tmp_path: Path):
    lib.clear_library_cache()
    root = tmp_path / "cache_lib"
    root.mkdir()
    novel1 = root / "Novel 1"
    novel1.mkdir()
    (novel1 / "Chapter_01.txt").write_text("Isi 1", encoding="utf-8")

    # Initial load
    novels1 = lib.load_library(str(root))
    assert len(novels1) == 1
    assert novels1[0].judul == "Novel 1"

    # Consecutive load returns cached catalog
    novels2 = lib.load_library(str(root))
    assert len(novels2) == 1
    assert novels2[0].judul == "Novel 1"

    # Add a new novel folder -> cache is invalidated
    novel2 = root / "Novel 2"
    novel2.mkdir()
    (novel2 / "Chapter_01.txt").write_text("Isi 2", encoding="utf-8")

    novels3 = lib.load_library(str(root))
    assert len(novels3) == 2
    titles = [n.judul for n in novels3]
    assert "Novel 1" in titles
    assert "Novel 2" in titles


def test_build_chapter_list_caching(tmp_path: Path):
    lib.clear_library_cache()
    folder = tmp_path / "Novel Test"
    folder.mkdir()
    (folder / "Chapter_01.txt").write_text("Bab 1", encoding="utf-8")

    chaps1 = lib.build_chapter_list(str(folder))
    assert len(chaps1) == 1
    assert chaps1[0].title == "Chapter 01"

    # Second call returns cached list
    chaps2 = lib.build_chapter_list(str(folder))
    assert len(chaps2) == 1

    # Adding file invalidates cache
    (folder / "Chapter_02.txt").write_text("Bab 2", encoding="utf-8")
    chaps3 = lib.build_chapter_list(str(folder))
    assert len(chaps3) == 2
    assert chaps3[1].title == "Chapter 02"


def test_natural_sort_key_mixed_types(tmp_path: Path):
    lib.clear_library_cache()
    root = tmp_path / "mixed_lib"
    root.mkdir()
    for folder_name in ["100_Novel", "My Novel", "2_Novel", "Alpha Novel"]:
        f = root / folder_name
        f.mkdir()
        (f / "Chapter_01.txt").write_text("Konten", encoding="utf-8")

    novels = lib.load_library(str(root))
    assert len(novels) == 4
    titles = [n.judul for n in novels]
    # Numeric names sort first naturally: 2_Novel before 100_Novel, followed by Alpha Novel, My Novel
    assert titles == ["2_Novel", "100_Novel", "Alpha Novel", "My Novel"]


def test_indexed_novel_fallback_to_disk_chapters(tmp_path: Path):
    import json
    lib.clear_library_cache()
    root = tmp_path / "indexed_disk_fallback"
    root.mkdir()
    novel_dir = root / "Water-Attribute Magician"
    novel_dir.mkdir()
    for i in range(1, 97):
        (novel_dir / f"Chapter_{i:02d}.txt").write_text(f"Bab {i}", encoding="utf-8")

    # library_index.json lists the novel, but chapters list is empty in JSON
    index_file = root / "library_index.json"
    index_file.write_text(json.dumps({
        "novels": [
            {"id": "water-attribute-magician", "judul": "Water-Attribute Magician", "folder_path": "Water-Attribute Magician"}
        ],
        "chapters": []
    }), encoding="utf-8")

    novels = lib.load_library(str(root))
    assert len(novels) == 1
    assert novels[0].judul == "Water-Attribute Magician"
    assert novels[0].chapter_count == 96
