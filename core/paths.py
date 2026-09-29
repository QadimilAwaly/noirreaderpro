"""
Resolusi path library & safe-join (cegah traversal path).

Urutan resolusi library_roots:
  0. Environment variable (NOIR_LIBRARY_ROOTS / NOIR_LIBRARY_ROOT / LIBRARY_ROOTS / LIBRARY_ROOT)
  1. device_config.json (hasil set UI) -> library_roots / library_root (list atau string)
  2. config.json (ter-commit, bisa diedit manual) -> library_roots / library_root / global_storage_path
  3. fallback ./Novel_Library (relatif DATA_DIR / BASE_DIR)
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, List, Union

import core.config


def get_device_config_path() -> Path:
    getter = getattr(core.config, "get_device_config_path", None)
    if callable(getter):
        return getter()
    return getattr(core.config, "DEVICE_CONFIG_JSON", core.config.BASE_DIR / "device_config.json")


def get_config_path() -> Path:
    getter = getattr(core.config, "get_config_path", None)
    if callable(getter):
        return getter()
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


def normalize_path(p: Union[str, Path, Any]) -> Path:
    """
    Normalisasi path: ekspansi user (~), environment variables ($VAR / %VAR%),
    dan resolve path relatif terhadap DATA_DIR / BASE_DIR jika ada.
    """
    if isinstance(p, Path):
        s = str(p)
    else:
        s = str(p).strip().strip('"').strip("'")

    expanded = os.path.expanduser(os.path.expandvars(s))
    path_obj = Path(expanded)

    if not path_obj.is_absolute():
        data_dir_getter = getattr(core.config, "get_data_dir", None)
        data_dir = data_dir_getter() if callable(data_dir_getter) else getattr(core.config, "DATA_DIR", core.config.BASE_DIR)
        candidate = (data_dir / path_obj).resolve()
        if candidate.exists():
            return candidate
        base_dir_getter = getattr(core.config, "get_base_dir", None)
        base_dir = base_dir_getter() if callable(base_dir_getter) else getattr(core.config, "BASE_DIR", Path.cwd())
        candidate_base = (base_dir / path_obj).resolve()
        if candidate_base.exists():
            return candidate_base
        return path_obj.resolve()
    return path_obj.resolve()


def _extract_paths(val: Any) -> List[str]:
    """Ekstrak list path dari string atau list, mendukung pemisah ; atau baris baru atau koma."""
    if not val:
        return []

    raw_items: List[str] = []
    if isinstance(val, (list, tuple, set)):
        for item in val:
            if isinstance(item, str):
                raw_items.append(item)
            elif item:
                raw_items.append(str(item))
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
    # 0. Environment variable override
    env_paths_raw = (
        os.environ.get("NOIR_LIBRARY_ROOTS")
        or os.environ.get("NOIR_LIBRARY_ROOT")
        or os.environ.get("LIBRARY_ROOTS")
        or os.environ.get("LIBRARY_ROOT")
    )
    if env_paths_raw:
        env_paths = _extract_paths(env_paths_raw)
        valid_env: List[str] = []
        for p in env_paths:
            pp = normalize_path(p)
            if pp.exists() and pp.is_dir():
                resolved = str(pp.resolve())
                if resolved not in valid_env:
                    valid_env.append(resolved)
        if valid_env:
            return valid_env

    # 1. device_config.json override
    dev = load_device_config()
    dev_paths = _extract_paths(dev.get("library_roots") or dev.get("library_root"))
    valid_dev: List[str] = []
    for p in dev_paths:
        pp = normalize_path(p)
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
        pp = normalize_path(p)
        if pp.exists() and pp.is_dir():
            resolved = str(pp.resolve())
            if resolved not in valid_cfg:
                valid_cfg.append(resolved)
    if valid_cfg:
        return valid_cfg

    # 3. fallback default
    fallback_getter = getattr(core.config, "get_default_library_fallback", None)
    if callable(fallback_getter):
        fallback_raw = fallback_getter()
    else:
        fallback_raw = getattr(core.config, "DEFAULT_LIBRARY_FALLBACK", core.config.BASE_DIR / "Novel_Library")
    fallback = normalize_path(fallback_raw)
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
        part_str = str(part)
        # cegah absolute, traversal eksplisit, atau Windows drive di segmen
        if Path(part_str).is_absolute() or ".." in Path(part_str).parts or re.match(r"^[a-zA-Z]:", part_str):
            return None
        target = target / part_str
    target = target.resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError:
        return None  # keluar dari base
    return str(target)
