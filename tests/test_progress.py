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
