import json
from pathlib import Path

import core.config
from core import paths


def test_resolve_default_fallback_when_empty(tmp_path: Path, monkeypatch):
    # config.json & device_config kosong -> fallback ./Novel_Library tidak ada -> ''
    monkeypatch.setattr(core.config, "CONFIG_JSON", tmp_path / "config.json")
    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", tmp_path / "device_config.json")
    monkeypatch.setattr(core.config, "DEFAULT_LIBRARY_FALLBACK", tmp_path / "Novel_Library")
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "device_config.json").write_text("{}", encoding="utf-8")
    assert paths.resolve_library_roots() == []
    assert paths.resolve_library_root() == ""


def test_resolve_from_config_json(tmp_path: Path, monkeypatch):
    lib = tmp_path / "Lib"
    lib.mkdir()
    (tmp_path / "config.json").write_text(json.dumps({"library_root": str(lib)}), encoding="utf-8")
    monkeypatch.setattr(core.config, "CONFIG_JSON", tmp_path / "config.json")
    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", tmp_path / "device_config.json")
    monkeypatch.setattr(core.config, "DEFAULT_LIBRARY_FALLBACK", tmp_path / "Novel_Library")
    assert paths.resolve_library_root() == str(lib.resolve())
    assert paths.resolve_library_roots() == [str(lib.resolve())]


def test_resolve_multi_roots_from_config_json(tmp_path: Path, monkeypatch):
    lib1 = tmp_path / "Lib1"; lib1.mkdir()
    lib2 = tmp_path / "Lib2"; lib2.mkdir()
    (tmp_path / "config.json").write_text(json.dumps({"library_roots": [str(lib1), str(lib2)]}), encoding="utf-8")
    monkeypatch.setattr(core.config, "CONFIG_JSON", tmp_path / "config.json")
    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", tmp_path / "device_config.json")
    monkeypatch.setattr(core.config, "DEFAULT_LIBRARY_FALLBACK", tmp_path / "Novel_Library")
    assert paths.resolve_library_roots() == [str(lib1.resolve()), str(lib2.resolve())]


def test_resolve_device_overrides_config(tmp_path: Path, monkeypatch):
    a = tmp_path / "A"; a.mkdir()
    b = tmp_path / "B"; b.mkdir()
    (tmp_path / "config.json").write_text(json.dumps({"library_root": str(a)}), encoding="utf-8")
    (tmp_path / "device_config.json").write_text(json.dumps({"library_root": str(b)}), encoding="utf-8")
    monkeypatch.setattr(core.config, "CONFIG_JSON", tmp_path / "config.json")
    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", tmp_path / "device_config.json")
    monkeypatch.setattr(core.config, "DEFAULT_LIBRARY_FALLBACK", tmp_path / "Novel_Library")
    assert paths.resolve_library_root() == str(b.resolve())
    assert paths.resolve_library_roots() == [str(b.resolve())]


def test_safe_join_blocks_traversal(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    assert paths.safe_join(str(root), "sub", "file.txt") is not None
    assert paths.safe_join(str(root), "..", "evil.txt") is None
    assert paths.safe_join(str(root), "/abs/path") is None
