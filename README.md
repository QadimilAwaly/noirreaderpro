# Noir Reader Pro

> **Pembaca Novel Lokal — Bersih, Cepat, dan Intuitif.**  
> Arsitektur FastAPI + frontend modular, dirancang untuk pengalaman membaca yang fokus tanpa gangguan. Kompatibel penuh dengan ekosistem Novel Translator Pro.

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
Buka peramban ke `http://127.0.0.1:3030`.

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

Edit `config.json` untuk menetapkan direktori koleksi:

```json
{
  "library_roots": [
    "/sdcard/Download/Novel_Library"
  ]
}
```

Field `global_storage_path` juga dikenali, selaras dengan struktur translator.

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

*Noir Reader Pro v1.0.0 — Dibangun untuk pembaca yang menghargai privasi, performa, dan estetika minimalis.*
