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
    parent = filepath.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
    lock = _lock_for(str(filepath))
    payload_bytes = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    tmp_path = filepath.with_suffix(filepath.suffix + f".tmp_{os.getpid()}")
    with lock:
        try:
            with open(tmp_path, "wb") as f:
                f.write(payload_bytes)
            os.replace(tmp_path, filepath)
        except Exception:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise

def load_json(filepath: str | Path, default: dict | None = None) -> dict:
    filepath = Path(filepath)
    if not filepath.exists():
        return default if default is not None else {}
    lock = _lock_for(str(filepath))
    with lock:
        try:
            with filepath.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else (default or {})
        except (json.JSONDecodeError, OSError, ValueError):
            return default if default is not None else {}
