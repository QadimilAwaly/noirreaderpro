import json
import tempfile
from pathlib import Path

from core import storage


def test_safe_save_json_atomic(tmp_path: Path):
    f = tmp_path / "x.json"
    storage.safe_save_json(f, {"a": 1})
    assert json.loads(f.read_text(encoding="utf-8")) == {"a": 1}


def test_load_json_missing_returns_default(tmp_path: Path):
    assert storage.load_json(tmp_path / "nope.json", {"d": 1}) == {"d": 1}


def test_save_then_load_roundtrip(tmp_path: Path):
    f = tmp_path / "y.json"
    storage.safe_save_json(f, {"k": "v"})
    assert storage.load_json(f) == {"k": "v"}
