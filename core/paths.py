"""
Resolusi path library & safe-join (cegah traversal path).

Urutan resolusi library_roots:
  1. device_config.json (hasil set UI) -> library_roots / library_root (list atau string)
  2. config.json (ter-commit, bisa diedit manual) -> library_roots / library_root / global_storage_path
  3. fallback ./Novel_Library (relatif cwd)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, List

import core.config


def get_device_config_path() -> Path:
    return getattr(core.config, "DEVICE_CONFIG_JSON", core.config.BASE_DIR / "device_config.json")


def get_config_path() -> Path:
    return getattr(core.config, "CONFIG_JSON", core.config.BASE_DIR / "config.json")


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError, ValueError):
        return {}


def load_device_config() -> dict:
    return _read_json(get_device_config_path())


def save_device_config(data: dict) -> None:
    target_path = get_device_config_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = target_path.with_suffix(target_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(target_path)


def _extract_paths(val: Any) -> List[str]:
    """Ekstrak list path dari string atau list, mendukung pemisah ; atau baris baru atau koma."""
    if not val:
        return []

    raw_items: List[str] = []
    if isinstance(val, (list, tuple)):
        for item in val:
            if isinstance(item, str):
                raw_items.append(item)
    elif isinstance(val, str):
        # Pisahkan berdasar baris baru atau semicolon (;)
        for part in re.split(r"[;\r\n]+", val):
            if part.strip():
                raw_items.append(part.strip())

    cleaned: List[str] = []
    for item in raw_items:
        s = item.strip().strip('"').strip("'").strip()
        if s:
            cleaned.append(s)
    return cleaned


def resolve_library_roots() -> List[str]:
    """Kembalikan list path absolut library roots yang valid (tanpa duplikat)."""
    # 1. device_config.json override
    dev = load_device_config()
    dev_paths = _extract_paths(dev.get("library_roots") or dev.get("library_root"))
    valid_dev: List[str] = []
    for p in dev_paths:
        pp = Path(p)
        if pp.exists() and pp.is_dir():
            resolved = str(pp.resolve())
            if resolved not in valid_dev:
                valid_dev.append(resolved)
    if valid_dev:
        return valid_dev

    # 2. config.json committed
    cfg = _read_json(get_config_path())
    cfg_paths = _extract_paths(
        cfg.get("library_roots") or cfg.get("library_root") or cfg.get("global_storage_path")
    )
    valid_cfg: List[str] = []
    for p in cfg_paths:
        pp = Path(p)
        if pp.exists() and pp.is_dir():
            resolved = str(pp.resolve())
            if resolved not in valid_cfg:
                valid_cfg.append(resolved)
    if valid_cfg:
        return valid_cfg

    # 3. fallback default
    fallback = getattr(core.config, "DEFAULT_LIBRARY_FALLBACK", core.config.BASE_DIR / "Novel_Library")
    if fallback.exists() and fallback.is_dir():
        return [str(fallback.resolve())]

    return []


def resolve_library_root() -> str:
    """Kembalikan path absolut library_root utama (pertama yang valid), atau '' jika belum diset."""
    roots = resolve_library_roots()
    return roots[0] if roots else ""


def safe_join(root: str, *parts: str) -> str | None:
    """
    Gabungkan root dengan parts, pastikan hasil TETAP di dalam root.
    Tolak traversal (..) dan path absolut di parts. Kembalikan None jika tidak aman.
    """
    if not root:
        return None
    base = Path(root).resolve()
    target = base
    for part in parts:
        if not part:
            continue
        # cegah absolute atau traversal eksplisit di segmen
        if Path(part).is_absolute() or ".." in Path(part).parts:
            return None
        target = target / part
    target = target.resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError:
        return None  # keluar dari base
    return str(target)
