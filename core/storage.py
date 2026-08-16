"""
Penyimpanan JSON atomic (porting dari reader lama + perbaikan).

- Tulis ke temp file lalu os.replace (atomic di Unix & Windows).
- Lock per-file untuk thread safety (FastAPI async tapi handler sync).
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path

_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(path: str) -> threading.Lock:
    with _locks_guard:
        if path not in _locks:
            _locks[path] = threading.Lock()
        return _locks[path]


def safe_save_json(filepath: str | Path, data: dict) -> None:
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    lock = _lock_for(str(filepath.resolve()))
    with lock:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(filepath.parent), prefix=".tmp_", suffix=".json"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, str(filepath))
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise


def load_json(filepath: str | Path, default: dict | None = None) -> dict:
    filepath = Path(filepath)
    if not filepath.exists():
        return default if default is not None else {}
    lock = _lock_for(str(filepath.resolve()))
    with lock:
        try:
            with filepath.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else (default or {})
        except (json.JSONDecodeError, OSError, ValueError):
            return default if default is not None else {}
