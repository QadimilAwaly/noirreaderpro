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
    assert paths.safe_join(str(root), "C:evil.txt") is None


def test_resolve_from_env_var(tmp_path: Path, monkeypatch):
    lib = tmp_path / "EnvLib"
    lib.mkdir()
    monkeypatch.setenv("NOIR_LIBRARY_ROOTS", str(lib))
    monkeypatch.setattr(core.config, "CONFIG_JSON", tmp_path / "config.json")
    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", tmp_path / "device_config.json")
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "device_config.json").write_text("{}", encoding="utf-8")
    assert paths.resolve_library_roots() == [str(lib.resolve())]
    assert paths.resolve_library_root() == str(lib.resolve())


def test_resolve_expand_env_vars(tmp_path: Path, monkeypatch):
    target = tmp_path / "MyNovels"
    target.mkdir()
    monkeypatch.setenv("TEST_NOVEL_FOLDER", str(target))
    monkeypatch.setattr(core.config, "CONFIG_JSON", tmp_path / "config.json")
    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", tmp_path / "device_config.json")
    (tmp_path / "config.json").write_text(json.dumps({"library_roots": ["$TEST_NOVEL_FOLDER"]}), encoding="utf-8")
    (tmp_path / "device_config.json").write_text("{}", encoding="utf-8")
    assert paths.resolve_library_roots() == [str(target.resolve())]


def test_normalize_relative_path(tmp_path: Path, monkeypatch):
    rel_dir = tmp_path / "LocalNovels"
    rel_dir.mkdir()
    monkeypatch.setattr(core.config, "DATA_DIR", tmp_path)
    normalized = paths.normalize_path("LocalNovels")
    assert normalized == rel_dir.resolve()


def test_config_host_and_port(tmp_path: Path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    dev_cfg_file = tmp_path / "device_config.json"
    monkeypatch.setattr(core.config, "CONFIG_JSON", cfg_file)
    monkeypatch.setattr(core.config, "DEVICE_CONFIG_JSON", dev_cfg_file)

    # 1. Defaults when configs are empty
    cfg_file.write_text("{}", encoding="utf-8")
    dev_cfg_file.write_text("{}", encoding="utf-8")
    assert core.config.get_host() == "127.0.0.1"
    assert core.config.get_port() == 3030

    # 2. Configured in config.json
    cfg_file.write_text(json.dumps({"host": "0.0.0.0", "port": 8080}), encoding="utf-8")
    assert core.config.get_host() == "0.0.0.0"
    assert core.config.get_port() == 8080

    # 3. Device config overrides config.json
    dev_cfg_file.write_text(json.dumps({"host": "192.168.1.50", "port": 9090}), encoding="utf-8")
    assert core.config.get_host() == "192.168.1.50"
    assert core.config.get_port() == 9090

    # 4. Env vars override both
    monkeypatch.setenv("NOIR_HOST", "10.0.0.1")
    monkeypatch.setenv("NOIR_PORT", "4040")
    assert core.config.get_host() == "10.0.0.1"
    assert core.config.get_port() == 4040
