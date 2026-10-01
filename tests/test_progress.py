from pathlib import Path

from services import progress as prog


def test_bookmark_crud(tmp_path: Path):
    folder = tmp_path / "novel"
    folder.mkdir()
    prog.save_progress(str(folder), prog.Progress(current_chapter_index=2))
    assert prog.load_progress(str(folder)).current_chapter_index == 2

    bm = prog.add_bookmark(str(folder), 3, "Climax")
    assert bm.chapter_index == 3
    loaded = prog.load_progress(str(folder))
    assert len(loaded.bookmarks) == 1

    assert prog.remove_bookmark(str(folder), bm.id) is True
    assert prog.load_progress(str(folder)).bookmarks == []


def test_progress_persists_to_folder(tmp_path: Path):
    folder = tmp_path / "novel"
    folder.mkdir()
    prog.add_bookmark(str(folder), 0, "A")
    # file harus ada di dalam folder
    files = list(folder.iterdir())
    assert any(f.name.endswith("_progress.json") for f in files)


def test_load_progress_fallback_to_last_bookmark(tmp_path: Path):
    folder = tmp_path / "novel_bm"
    folder.mkdir()
    # Create progress file with current_chapter_index = 0 and bookmarks at chapter 0 and 2
    p_file = folder / f".{folder.name}_progress.json"
    p_file.write_text(
        '{"current_chapter_index": 0, "bookmarks": [{"id": "b1", "chapter_index": 0}, {"id": "b2", "chapter_index": 2}]}',
        encoding="utf-8",
    )
    loaded = prog.load_progress(str(folder))
    assert loaded.current_chapter_index == 2
