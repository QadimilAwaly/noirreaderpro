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

_PID = os.getpid()
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(path: str) -> threading.Lock:
    with _locks_guard:
        if path not in _locks:
            _locks[path] = threading.Lock()
        return _locks[path]


def safe_save_json(filepath: str | Path, data: dict) -> None:
    f_str = str(filepath)
    lock = _lock_for(f_str)
    payload_bytes = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    tmp_path = f_str + f".tmp_{_PID}"
    with lock:
        try:
            with open(tmp_path, "wb") as f:
                f.write(payload_bytes)
        except FileNotFoundError:
            parent = os.path.dirname(f_str)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(tmp_path, "wb") as f:
                f.write(payload_bytes)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        try:
            os.replace(tmp_path, f_str)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


def load_json(filepath: str | Path, default: dict | None = None) -> dict:
    f_str = str(filepath)
    lock = _lock_for(f_str)
    with lock:
        try:
            with open(f_str, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else (default or {})
        except (FileNotFoundError, OSError, json.JSONDecodeError, ValueError):
            return default if default is not None else {}
