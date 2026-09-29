# Noir Reader Pro

> **Pembaca Novel Lokal — Bersih, Cepat, dan Intuitif.**  
> Arsitektur FastAPI + frontend modular, dirancang untuk pengalaman membaca yang fokus tanpa gangguan. Kompatibel penuh dengan ekosistem Novel Translator Pro.  
> 🌐 **Landing Page:** [https://qadimilawaly.github.io/noirreaderpro/](https://qadimilawaly.github.io/noirreaderpro/)

---

## Ringkasan Produk

Noir Reader Pro adalah aplikasi pembaca novel lokal berbasis web yang mengutamakan kecepatan, privasi data, dan kenyamanan visual. Dibangun di atas Python (FastAPI) dengan frontend responsif, aplikasi ini membaca koleksi dari berbagai format — `.txt`, `.md`, `.epub`, serta katalog hasil terjemahan — tanpa memerlukan server eksternal atau koneksi internet aktif saat membaca.

---

## Fitur Utama

- **Katalog Otomatis** — Deteksi koleksi dari `library_index.json` (hasil translator) atau pemindaian folder langsung (mode legacy).
- **Dukungan Multi-Format** — `.txt`, `.md`, `.epub` (parser bawaan tanpa dependensi berat), serta integrasi dengan hasil terjemahan (`Chapter_NN.md` + `library_index.json`).
- **Multi-Folder Library** — Konfigurasi beberapa direktori koleksi melalui `library_roots` di `config.json`.
- **Resume Otomatis** — Melanjutkan membaca ke novel dan bab terakhir setiap kali aplikasi dibuka.
- **Bookmark Per-Novel** — Penanda bab disimpan in-folder, sinkron otomatis melalui layanan seperti Resilio Sync.
- **Tema Soft Noir** — Antarmuka terang/gelap dengan kontras lembut, pengaturan font, jarak baris, indentasi, dan margin secara real-time.
- **Panel Responsif** — Navigasi koleksi, daftar bab, dan pengaturan tampilan dapat disembunyikan atau ditampilkan sesuai kebutuhan, responsif di perangkat desktop maupun mobile.
- **Navigasi Cepat** — Shortcut keyboard (`← →`, `T`, `B`, `N`, `C`, `P`, `Esc`) untuk akses efisien tanpa mengangkat tangan dari papan ketik.

---

## Persyaratan & Instalasi

**Prasyarat:** Python 3.11+

```bash
pip install -r requirements.txt
python main.py
```
Buka peramban ke `http://127.0.0.1:3030` (Aplikasi Reader) atau `http://127.0.0.1:3030/landing` (Landing Page).

### Termux (Android)
```bash
pkg install python
pip install -r requirements.txt
termux-setup-storage   # akses penyimpanan bersama
python main.py
```
Sesuaikan `library_root` di `config.json` (mis. `/sdcard/Download/Novel_Library`) sebelum menjalankan.

---

## Konfigurasi Cepat

### 1. File `config.json`
Edit `config.json` untuk menetapkan host, port, dan direktori koleksi novel:

```json
{
  "host": "127.0.0.1",
  "port": 3030,
  "library_roots": [
    "./Novel_Library"
  ]
}
```

- Path mendukung format relatif (mis. `./Novel_Library`), ekspansi `~` (home user), dan environment variable (mis. `$HOME/Novels`).
- Field `library_root` dan `global_storage_path` juga tetap didukung untuk kompatibilitas.

### 2. Opsi Command-Line (CLI)
Anda dapat menentukan host dan port saat menjalankan server:
```bash
python main.py --host 0.0.0.0 --port 8080
python app_desktop.py --host 127.0.0.1 --port 3030
```

### 3. Environment Variables
Konfigurasi juga dapat dikendalikan sepenuhnya melalui environment variables:
- `NOIR_HOST` atau `HOST` — Host/IP server bind (default: `127.0.0.1`).
- `NOIR_PORT` atau `PORT` — Port server (default: `3030`).
- `NOIR_LIBRARY_ROOTS` atau `NOIR_LIBRARY_ROOT` — Path direktori pustaka novel.
- `NOIR_DATA_DIR` — Direktori penyimpanan data & konfigurasi runtime.
- `NOIR_CONFIG_FILE` — Lokasi kustom file `config.json`.

---

## Pengelolaan Daya & Proses (Termux)

Aplikasi berjalan sebagai server lokal `uvicorn` di port 3030. Untuk menghemat daya baterai perangkat:

- **Hentikan foreground:** `Ctrl + C`
- **Hentikan proses latar belakang:** `pkill -f "python main.py"`
- **Praktik terbaik:** Jalankan server secara on-demand saat sesi membaca, lalu hentikan setelah selesai.

---

## Dukungan Format

| Sumber | Cara Dibaca | Teks Asli |
|--------|-------------|-----------|
| `library_index.json` (translator) | Katalog + isi bab dari `chapters[]` | Ya (`teks_asli`) |
| `Chapter_NN.md` (translator) | Bagian "Hasil Terjemahan" / "Teks Asli" | Ya |
| `.txt` (legacy) | Teks polos, format dasar (`**tebal**`, `*miring*`) | Tidak |
| `.epub` | Parser bawaan (`zipfile` + `xml` + `html.parser`) | Tidak |

File dalam folder novel dapat dicampur (`.txt` / `.md` / `.epub`); semua digabung dan diurutkan secara natural.

---

## Arsitektur

```
core/       Konfigurasi, resolusi jalur (safe_join), penyimpanan atomik (JSON)
models/     Model data novel dan pengaturan (Pydantic)
services/   Katalog pustaka, pembaca isi, parser EPUB, penyimpanan bookmark
api/        Router: library, chapter, progress, pengaturan
frontend/   HTML + CSS (tema/layout) + JS (manajemen API/state/UI)
tests/      Pytest: storage, paths, library, reader, epub, progress, API
```

---

## Prinsip Desain UX

Noir Reader Pro mengikuti 10 heuristik kegunaan Nielsen — mulai dari status sistem yang selalu terlihat, kontrol penuh pengguna, konsistensi antarmuka, hingga pemulihan kesalahan yang jelas dan dokumentasi yang membantu pengguna baru memahami konfigurasi dalam hitungan menit.

---

## Shortcut Keyboard

| Tombol | Fungsi |
|-------|--------|
| `←` / `→` / `h` / `l` | Bab sebelumnya / berikutnya |
| `T` | Ganti tema (terang / gelap) |
| `B` | Buka panel bookmark |
| `N` | Panel koleksi novel |
| `C` | Panel daftar bab |
| `P` | Pengaturan tampilan |
| `Esc` | Tutup panel aktif |

---

## Lisensi

MIT License — lihat file `LICENSE` untuk ketentuan lengkap.

---

## Kontribusi & Umpan Balik

Laporan masalah, permintaan fitur, atau kontribusi kode diterima melalui repositori proyek. Pastikan semua perubahan disertai pengujian (`pytest`) sebelum diajukan.
---

## Disclaimer

> **Catatan:** Ini adalah *vibe coding project* pribadi seorang yang bukan background programmer. Dibuat untuk kebutuhan membaca novel lokal secara mandiri, fokus, dan nyaman.

---

*Noir Reader Pro v1.0.0 — Dibangun untuk pembaca yang menghargai privasi, performa, dan estetika minimalis.*
