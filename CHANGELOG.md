# Changelog

## 1.2.0 (2026-10-02)

### Fitur Baru & Tipografi
- **Dukungan Penuh LaTeX Math:** Rendering otomatis formula ilmiah inline (`$E = mc^2$`, `$E$`, `$m$`, `$c$`, `$H_2O$`) dan display block (`$$...$$`) menjadi HTML semantik (`<var>`, `<sup>`, `<sub>`, pecahan `\frac`, akar `\sqrt`, simbol Yunani `\alpha`, `\beta`, `\Delta`, operator `\pm`, `\times`, `\cdot`, `\leq`, `\approx`, dll.) yang bekerja 100% offline tanpa dependensi eksternal, lengkap dengan proteksi nilai mata uang (`$100`).
- **Dukungan Rumus Kimia & Formula:** Format penulisan formula kimia seperti `H<sub>2</sub>O`, `CO<sub>2</sub>`, dan markdown subscript `H~2~O` serta superscript `10^5^` / `x^2^` ditampilkan rapi dengan perataan baseline proporsional tanpa merusak tinggi baris (*line-height*).
- **Dukungan Entitas HTML & Simbol Khusus:** Konversi otomatis entitas HTML hasil terjemahan/web scraping (`&mdash;`, `&hellip;`, `&ldquo;`, `&rdquo;`, `&deg;C`, dll.) menjadi karakter Unicode asli.
- **Tipografi Lanjutan:** Dukungan inline formatting untuk `<u>garis bawah</u>`, `<del>coret</del>`, `<mark>stabilo</mark>`, `` `kode` ``, dan furigana/ruby khas novel (`<ruby>漢字<rt>かんじ</rt></ruby>` dan `|漢字《かんじ》`).
- **Pembaca Berkas Multi-Encoding:** Deteksi dan pembersihan otomatis BOM UTF-8 (`utf-8-sig`) serta fallback ke Windows-1252/ANSI dan UTF-16 agar karakter spesial dari Notepad/Word tidak rusak menjadi tanda tanya pengganti.
- **Dukungan Sub/Sup pada EPUB:** Ekstraksi bab EPUB kini mempertahankan tag inline formatting (`<sub>`, `<sup>`, dll.).

### Perbaikan Bug
- **Perbaikan Perhitungan Chapter Count:** Menyelesaikan bug di mana novel terindeks yang memiliki bab di folder fisik disk menampilkan '0 chapter' di kartu novel (kini otomatis memeriksa folder fisik dan menyinkronkan jumlah bab ke kartu DOM).
- **Eliminasi Auto-Advance saat Reopen/Reload:** Menghapus fungsi background prefetching spekulatif yang berpotensi memajukan posisi baca ke bab berikutnya.
- **Preservasi Bab Aktif saat Resume:** Memastikan posisi baca terakhir (`current_chapter_index`) selalu dipertahankan secara akurat saat memuat ulang halaman atau membuka kembali aplikasi.
- **Bypass Browser Static Asset Cache:** Menambahkan query string versi (`?v=1.2.1`) pada file JavaScript dan CSS di antarmuka web untuk mencegah peramban menggunakan kode usang dari cache.

### Performa & Efisiensi Daya (Autoresearch Sesi #2)
- **-23.1% Total Latency Reduction:** Waktu respons terpangkas dari 10,328ms ke 7,943ms.
- **-21.7% Active CPU Time Reduction:** Menghemat daya baterai perangkat Android Termux & desktop secara drastis.
- **Universal 30x Faster Model Serialization:** Metode `.to_dict()` langsung berbasis `__dict__` pada seluruh model data (`NovelInfo`, `ChapterInfo`, `ChapterContent`, `Bookmark`, `Progress`), memangkas overhead rekursif Pydantic `model_dump()`.
- **Short-Circuit Regex Formatting:** Akselerasi parsing markdown hingga 3.22x lipat dengan evaluasi cepat berbasis C SIMD.
- **Direct Storage I/O:** Mengganti pengecekan `exists()` redundant dengan `try/open` direct syscalls pada pembacaan dan penulisan JSON.
- **EPUB In-Memory Spine Caching:** Menghindari penguraian XML berulang pada novel EPUB dengan caching urutan bab (5x lebih cepat).

## 1.1.1 (2026-10-01)
- **Perbaikan Tipe Data Pengurutan:** Mencegah `TypeError` antara `float` dan `str` pada `natural_sort_key` saat memindai nama folder pustaka campuran angka dan huruf.
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
