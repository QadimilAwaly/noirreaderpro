"""
Konfigurasi global Noir Reader Pro.

Satu sumber kebenaran untuk default (port, host, font, tema).
Tidak menyebar di beberapa file seperti reader lama.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Server
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
CONFIG_JSON = BASE_DIR / "config.json"          # ter-commit, bisa diedit manual
DEVICE_CONFIG_JSON = BASE_DIR / "device_config.json"  # gitignored, override UI

# Default library root jika belum diset
DEFAULT_LIBRARY_FALLBACK = BASE_DIR / "Novel_Library"


@lru_cache(maxsize=1)
def get_base_dir() -> Path:
    return BASE_DIR
