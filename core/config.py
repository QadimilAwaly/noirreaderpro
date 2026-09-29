"""
Konfigurasi global Noir Reader Pro.

Satu sumber kebenaran untuk default (port, host, font, tema).
Tidak menyebar di beberapa file seperti reader lama.
"""
from __future__ import annotations

import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

# Static bundle directory (handles PyInstaller temp extract folder)
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR

# Allow overriding DATA_DIR via environment variable
_env_data_dir = os.environ.get("NOIR_DATA_DIR") or os.environ.get("NOIR_CONFIG_DIR")
if _env_data_dir:
    DATA_DIR = Path(_env_data_dir).expanduser().resolve()

# Server defaults
DEFAULT_PORT = 3030
DEFAULT_HOST = "127.0.0.1"  # localhost only — cegah paparan jaringan

# Default tampilan (Soft Noir, default terang)
DEFAULT_FONT_SIZE = 16          # px
DEFAULT_LINE_SPACING = 1.7
DEFAULT_PARAGRAPH_INDENT = 28   # px
DEFAULT_PAGE_MARGIN = 24        # px
DEFAULT_READ_WIDTH = 720        # px (lebar kolom baca)
DEFAULT_THEME = "light"         # 'light' | 'dark'

# File config
CONFIG_JSON = (
    Path(os.environ["NOIR_CONFIG_FILE"]).expanduser().resolve()
    if os.environ.get("NOIR_CONFIG_FILE") or os.environ.get("NOIR_CONFIG_PATH")
    else DATA_DIR / "config.json"
)
DEVICE_CONFIG_JSON = (
    Path(os.environ["NOIR_DEVICE_CONFIG_FILE"]).expanduser().resolve()
    if os.environ.get("NOIR_DEVICE_CONFIG_FILE")
    else DATA_DIR / "device_config.json"
)
SETTINGS_JSON = (
    Path(os.environ["NOIR_SETTINGS_FILE"]).expanduser().resolve()
    if os.environ.get("NOIR_SETTINGS_FILE")
    else DATA_DIR / "reader_settings.json"
)

# Default library root jika belum diset
DEFAULT_LIBRARY_FALLBACK = (
    Path(os.environ["NOIR_LIBRARY_DIR"]).expanduser().resolve()
    if os.environ.get("NOIR_LIBRARY_DIR") or os.environ.get("NOIR_LIBRARY_FALLBACK")
    else DATA_DIR / "Novel_Library"
)


def get_data_dir() -> Path:
    """Kembalikan direktori data efektif."""
    env_dir = os.environ.get("NOIR_DATA_DIR") or os.environ.get("NOIR_CONFIG_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    module = sys.modules.get(__name__)
    if module and hasattr(module, "DATA_DIR") and module.DATA_DIR:
        return Path(module.DATA_DIR)
    return DATA_DIR


@lru_cache(maxsize=1)
def get_base_dir() -> Path:
    return BASE_DIR


def get_config_path() -> Path:
    """Kembalikan path config.json efektif."""
    env_file = os.environ.get("NOIR_CONFIG_FILE") or os.environ.get("NOIR_CONFIG_PATH")
    if env_file:
        return Path(env_file).expanduser().resolve()
    module = sys.modules.get(__name__)
    if module and hasattr(module, "CONFIG_JSON") and module.CONFIG_JSON:
        return Path(module.CONFIG_JSON)
    return get_data_dir() / "config.json"


def get_device_config_path() -> Path:
    """Kembalikan path device_config.json efektif."""
    env_file = os.environ.get("NOIR_DEVICE_CONFIG_FILE")
    if env_file:
        return Path(env_file).expanduser().resolve()
    module = sys.modules.get(__name__)
    if module and hasattr(module, "DEVICE_CONFIG_JSON") and module.DEVICE_CONFIG_JSON:
        return Path(module.DEVICE_CONFIG_JSON)
    return get_data_dir() / "device_config.json"


def get_settings_path() -> Path:
    """Kembalikan path reader_settings.json efektif."""
    env_file = os.environ.get("NOIR_SETTINGS_FILE")
    if env_file:
        return Path(env_file).expanduser().resolve()
    module = sys.modules.get(__name__)
    if module and hasattr(module, "SETTINGS_JSON") and module.SETTINGS_JSON:
        return Path(module.SETTINGS_JSON)
    return get_data_dir() / "reader_settings.json"


def get_default_library_fallback() -> Path:
    """Kembalikan path fallback direktori novel default."""
    env_dir = os.environ.get("NOIR_LIBRARY_DIR") or os.environ.get("NOIR_LIBRARY_FALLBACK")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    module = sys.modules.get(__name__)
    if module and hasattr(module, "DEFAULT_LIBRARY_FALLBACK") and module.DEFAULT_LIBRARY_FALLBACK:
        return Path(module.DEFAULT_LIBRARY_FALLBACK)
    return get_data_dir() / "Novel_Library"


def _read_config_value(key: str) -> Any:
    """Baca nilai konfigurasi dari device_config.json lalu config.json."""
    for path_func in (get_device_config_path, get_config_path):
        try:
            p = path_func()
            if p and p.exists():
                with p.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and key in data and data[key] is not None:
                        return data[key]
        except Exception:
            pass
    return None


def get_host() -> str:
    """
    Dapatkan host server yang dikonfigurasi.
    Urutan prioritas: NOIR_HOST / HOST env var -> device_config.json -> config.json -> DEFAULT_HOST
    """
    env_host = os.environ.get("NOIR_HOST") or os.environ.get("HOST")
    if env_host and env_host.strip():
        return env_host.strip()
    val = _read_config_value("host")
    if val and str(val).strip():
        return str(val).strip()
    module = sys.modules.get(__name__)
    return getattr(module, "DEFAULT_HOST", "127.0.0.1")


def get_port() -> int:
    """
    Dapatkan port server yang dikonfigurasi.
    Urutan prioritas: NOIR_PORT / PORT env var -> device_config.json -> config.json -> DEFAULT_PORT
    """
    env_port = os.environ.get("NOIR_PORT") or os.environ.get("PORT")
    if env_port:
        try:
            return int(env_port)
        except ValueError:
            pass
    val = _read_config_value("port")
    if val is not None:
        try:
            return int(val)
        except ValueError:
            pass
    module = sys.modules.get(__name__)
    return getattr(module, "DEFAULT_PORT", 3030)
