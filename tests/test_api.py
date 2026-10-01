from pathlib import Path
import json
from fastapi.testclient import TestClient
from main import app
import core.config

client = TestClient(app)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_no_cache_middleware_headers():
    # 1. Dynamic API endpoints must send no-store & no-cache
    api_res = client.get("/api/state")
    assert "no-cache" in api_res.headers.get("cache-control", "")
    assert "no-store" in api_res.headers.get("cache-control", "")

    # 2. Root HTML allows caching with ETag revalidation (not no-store)
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert "no-cache" in root_res.headers.get("cache-control", "")
    assert "no-store" not in root_res.headers.get("cache-control", "")

    # 3. Static assets allow browser caching (not no-store)
    static_res = client.get("/static/css/theme.css")
    assert static_res.status_code == 200
    assert "public" in static_res.headers.get("cache-control", "")
    assert "max-age" in static_res.headers.get("cache-control", "")
    assert "no-store" not in static_res.headers.get("cache-control", "")

    # 4. Landing HTML allows caching with revalidation
    landing_res = client.get("/landing")
    assert landing_res.status_code == 200
    assert "no-cache" in landing_res.headers.get("cache-control", "")
    assert "no-store" not in landing_res.headers.get("cache-control", "")
    assert "Noir Reader Pro" in landing_res.text

def test_settings_roundtrip(tmp_path: Path, monkeypatch):
    test_settings_file = tmp_path / "test_settings.json"
    import api.router_settings
    monkeypatch.setattr(api.router_settings, "SETTINGS_JSON", test_settings_file)

    # GET default
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert "font_size" in data
    assert "read_width" in data

    # POST new settings including read_width
    update = {
        "font_size": 20,
        "line_spacing": 1.9,
        "read_width": 840,
        "theme": "dark",
    }
    res = client.post("/api/settings", json=update)
    assert res.status_code == 200
    saved = res.json()
    assert saved["font_size"] == 20
    assert saved["line_spacing"] == 1.9
    assert saved["read_width"] == 840
    assert saved["theme"] == "dark"

    # Verify persistence on subsequent GET
    res = client.get("/api/settings")
    assert res.status_code == 200
    assert res.json()["read_width"] == 840
    assert res.json()["font_size"] == 20


def test_theme_endpoint(tmp_path: Path, monkeypatch):
    test_settings_file = tmp_path / "test_settings.json"
    import api.router_settings
    monkeypatch.setattr(api.router_settings, "SETTINGS_JSON", test_settings_file)

    res = client.post("/api/theme?theme=dark")
    assert res.status_code == 200
    assert res.json() == {"theme": "dark"}


def test_set_library_root_with_quotes(tmp_path: Path, monkeypatch):
    lib_dir = tmp_path / "My_Library"
    lib_dir.mkdir()
    novel_dir = lib_dir / "Novel 1"
    novel_dir.mkdir()
    (novel_dir / "Chapter_01.txt").write_text("Konten chapter satu.", encoding="utf-8")

    device_cfg = tmp_path / "device_config.json"
    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", device_cfg)

    # Post path wrapped in quotes
    quoted_path = f'"{str(lib_dir)}"'
    res = client.post("/api/set-library-root", json={"path": quoted_path})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["novel_count"] == 1

    # List novels
    res = client.get("/api/novels")
    assert res.status_code == 200
    novels = res.json()["novels"]
    assert len(novels) == 1
    assert novels[0]["judul"] == "Novel 1"


def test_multi_folder_library_api(tmp_path: Path, monkeypatch):
    root1 = tmp_path / "Folder_A"
    root1.mkdir()
    n1 = root1 / "Novel_Alpha"
    n1.mkdir()
    (n1 / "Chapter_01.txt").write_text("Isi Alpha.", encoding="utf-8")

    root2 = tmp_path / "Folder_B"
    root2.mkdir()
    n2 = root2 / "Novel_Beta"
    n2.mkdir()
    (n2 / "Chapter_01.txt").write_text("Isi Beta.", encoding="utf-8")

    device_cfg = tmp_path / "device_config.json"
    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", device_cfg)

    # Set multiple paths separated by semicolon
    multi_input = f"{str(root1)}; {str(root2)}"
    res = client.post("/api/set-library-root", json={"path": multi_input})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["novel_count"] == 2
    assert len(data["library_roots"]) == 2

    # Verify both novels can be listed
    res = client.get("/api/novels")
    assert res.status_code == 200
    novels = res.json()["novels"]
    assert len(novels) == 2
    titles = [n["judul"] for n in novels]
    assert "Novel_Alpha" in titles
    assert "Novel_Beta" in titles

    # Read chapters from novel in second folder
    beta_novel = next(n for n in novels if n["judul"] == "Novel_Beta")
    ch_res = client.get(f"/api/chapters?novel_id={beta_novel['id']}")
    assert ch_res.status_code == 200
    chapters = ch_res.json()["chapters"]
    assert len(chapters) == 1

    # Read chapter content from second folder
    content_res = client.get(f"/api/chapter?novel_id={beta_novel['id']}&ref=Chapter_01.txt")
    assert content_res.status_code == 200
    assert "Isi Beta." in content_res.json()["translation"]

    # Fallback test: Read chapter when novel_id is "null", "undefined", or missing
    fallback_res1 = client.get("/api/chapter?novel_id=null&ref=Chapter_01.txt")
    assert fallback_res1.status_code == 200
    assert fallback_res1.json()["ref"] == "Chapter_01.txt"

    fallback_res2 = client.get("/api/chapter?ref=Chapter_01.txt")
    assert fallback_res2.status_code == 200
    assert fallback_res2.json()["ref"] == "Chapter_01.txt"


def test_bookmarks_and_progress(tmp_path: Path, monkeypatch):
    lib_dir = tmp_path / "Library"
    lib_dir.mkdir()
    novel_dir = lib_dir / "Novel Progress"
    novel_dir.mkdir()
    (novel_dir / "Chapter_01.txt").write_text("Konten 1.", encoding="utf-8")
    (novel_dir / "Chapter_02.txt").write_text("Konten 2.", encoding="utf-8")

    device_cfg = tmp_path / "device_config.json"
    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", device_cfg)

    client.post("/api/set-library-root", json={"path": str(lib_dir)})
    novels = client.get("/api/novels").json()["novels"]
    novel_id = novels[0]["id"]

    # Mark read / bookmark
    res = client.post(
        f"/api/mark-read?novel_id={novel_id}",
        json={"chapter_index": 0, "label": "Bab 1 Pertama"},
    )
    assert res.status_code == 200
    prog = res.json()
    assert len(prog["bookmarks"]) == 1
    bm_id = prog["bookmarks"][0]["id"]
    assert prog["bookmarks"][0]["label"] == "Bab 1 Pertama"

    # Delete bookmark
    res = client.delete(f"/api/bookmark?novel_id={novel_id}&bookmark_id={bm_id}")
    assert res.status_code == 200
    assert res.json() == {"success": True}

    # Verify bookmark is removed
    res = client.get(f"/api/progress?novel_id={novel_id}")
    assert res.status_code == 200
    assert len(res.json()["bookmarks"]) == 0


def test_chapter_get_auto_bookmarks_single_write(tmp_path: Path, monkeypatch):
    lib_dir = tmp_path / "Library"
    lib_dir.mkdir()
    novel_dir = lib_dir / "Auto Novel"
    novel_dir.mkdir()
    (novel_dir / "Chapter_01.txt").write_text("Konten 1.", encoding="utf-8")
    (novel_dir / "Chapter_02.txt").write_text("Konten 2.", encoding="utf-8")

    device_cfg = tmp_path / "device_config.json"
    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", device_cfg)

    client.post("/api/set-library-root", json={"path": str(lib_dir)})
    novels = client.get("/api/novels").json()["novels"]
    novel_id = novels[0]["id"]

    # Track calls to save_progress
    from services import progress as prog_service
    save_calls = 0
    orig_save = prog_service.save_progress

    def counted_save(folder, p):
        nonlocal save_calls
        save_calls += 1
        return orig_save(folder, p)

    monkeypatch.setattr(prog_service, "save_progress", counted_save)
    import api.router_chapters
    monkeypatch.setattr(api.router_chapters.prog_service, "save_progress", counted_save)

    # GET /api/chapter for chapter 0
    res = client.get(f"/api/chapter?novel_id={novel_id}&ref=Chapter_01.txt")
    assert res.status_code == 200
    assert save_calls == 1  # Exactly ONE atomic write on chapter open

    # Verify progress and bookmark are auto-saved
    prog_res = client.get(f"/api/progress?novel_id={novel_id}")
    assert prog_res.status_code == 200
    prog_data = prog_res.json()
    assert prog_data["current_chapter_index"] == 0
    assert len(prog_data["bookmarks"]) == 1
    assert prog_data["bookmarks"][0]["chapter_index"] == 0
    assert prog_data["bookmarks"][0]["label"] == "Chapter 01"

    # Opening next chapter should update progress and auto-create second bookmark with exactly 1 write
    save_calls = 0
    res2 = client.get(f"/api/chapter?novel_id={novel_id}&ref=Chapter_02.txt")
    assert res2.status_code == 200
    assert save_calls == 1  # Exactly ONE atomic write
    prog_data2 = client.get(f"/api/progress?novel_id={novel_id}").json()
    assert prog_data2["current_chapter_index"] == 1
    assert len(prog_data2["bookmarks"]) == 2

    # Re-reading already bookmarked chapter updates index but does not duplicate bookmark (1 write)
    save_calls = 0
    res3 = client.get(f"/api/chapter?novel_id={novel_id}&ref=Chapter_01.txt")
    assert res3.status_code == 200
    assert save_calls == 1
    prog_data3 = client.get(f"/api/progress?novel_id={novel_id}").json()
    assert prog_data3["current_chapter_index"] == 0
    assert len(prog_data3["bookmarks"]) == 2
    # Prefetching chapter 2 must NOT trigger disk write or alter progress/bookmarks
    save_calls = 0
    res_prefetch = client.get(f"/api/chapter?novel_id={novel_id}&ref=Chapter_02.txt&prefetch=1")
    assert res_prefetch.status_code == 200
    assert save_calls == 0
    prog_data_prefetch = client.get(f"/api/progress?novel_id={novel_id}").json()
    assert prog_data_prefetch["current_chapter_index"] == 0
    assert len(prog_data_prefetch["bookmarks"]) == 2


def test_novels_api_caching_and_invalidation(tmp_path: Path, monkeypatch):
    from services.library import clear_library_cache
    from services.epub import clear_epub_cache
    clear_library_cache()
    clear_epub_cache()

    lib_dir = tmp_path / "Cached_Library"
    lib_dir.mkdir()
    novel1 = lib_dir / "Novel Alpha"
    novel1.mkdir()
    (novel1 / "Chapter_01.txt").write_text("Konten Alpha.", encoding="utf-8")

    device_cfg = tmp_path / "device_config.json"
    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", device_cfg)
    client.post("/api/set-library-root", json={"path": str(lib_dir)})

    # First GET /api/novels
    res1 = client.get("/api/novels")
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1["novels"]) == 1
    assert data1["novels"][0]["judul"] == "Novel Alpha"

    # Second GET /api/novels returns identical catalog from cache
    res2 = client.get("/api/novels")
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["novels"]) == 1
    assert data2["novels"][0]["id"] == data1["novels"][0]["id"]

    # Add a second novel -> cache invalidates automatically
    novel2 = lib_dir / "Novel Beta"
    novel2.mkdir()
    (novel2 / "Chapter_01.txt").write_text("Konten Beta.", encoding="utf-8")

    res3 = client.get("/api/novels")
    assert res3.status_code == 200
    data3 = res3.json()
    assert len(data3["novels"]) == 2
    titles = [n["judul"] for n in data3["novels"]]
    assert "Novel Alpha" in titles
    assert "Novel Beta" in titles
