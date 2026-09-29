# Changelog

## 1.1.0 (2026-09-29)

### Fitur & Pengaturan Fleksibel
- **Dukungan CLI & Environment Variables:** Opsi `--host` dan `-p`/`--port` pada `main.py` dan `app_desktop.py`, serta environment variables (`NOIR_HOST`, `NOIR_PORT`, `NOIR_LIBRARY_ROOTS`, `NOIR_DATA_DIR`, `NOIR_CONFIG_FILE`).
- **Jalur Portabel & Cross-Platform:** Menggantikan path absolut hardcoded dengan resolusi portabel (`./Novel_Library`), ekspansi `~` (home user) dan environment variables ($VAR / %VAR%).
- **Client-Side Cache & Idle Prefetch:** Menambahkan `_chapterCache` dan `requestIdleCallback` prefetch bab berikutnya untuk transisi instan tanpa loading spinner.
- **Differential DOM Updates:** Memperbarui kartu chapter aktif/terbaca secara selektif tanpa menghancurkan dan merender ulang ribuan elemen DOM.
- **Debounced Search:** Debounce 100ms pada filter pencarian novel dan chapter.

### Performa & Efisiensi Daya (Autoresearch)
- **-27.8% Total Latency Reduction:** Waktu respons terpangkas dari 14,150ms ke 10,212ms.
- **-28.1% Active CPU Time Reduction:** Penghematan baterai signifikan dengan pengurangan siklus CPU aktif.
- **-34.4% Progress Latency:** Optimasi auto-bookmark dan serialisasi progres tanpa syscalls berlebih.
- **Pure ASGI Middleware:** Menggantikan `BaseHTTPMiddleware` dengan `CacheControlASGIMiddleware` murni untuk memangkas overhead context-switching.
- **Memoized Library Root Resolution:** Memangkas lebih dari 1.000 panggilan stat syscalls per sesi membaca.

## 1.0.1

- Setup landing page, GitHub Pages, dan PyInstaller standalone Windows executable build workflow.

## 1.0.0 (pre-release)
- FastAPI server (port 3030) dengan frontend Soft Noir modular.
- Baca .txt, .md, .epub; resume otomatis; bookmark per-novel; multi-folder library.
- Konfigurasi library_root via config.json.
- Tema terang/gelap Soft Noir dengan pengaturan font dan jarak baris real-time.
