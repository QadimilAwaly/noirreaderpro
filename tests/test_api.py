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
    res = client.get("/")
    assert res.status_code == 200
    assert "no-cache" in res.headers.get("cache-control", "")
    assert "no-store" in res.headers.get("cache-control", "")


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
