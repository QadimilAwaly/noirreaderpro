# Noir Reader Pro

Pembaca novel lokal berarsitektur bersih (FastAPI + frontend modular, murni Python — ramah Termux).
Membaca koleksi dari **Novel_Library** (hasil translator: `library_index.json` + `Chapter_NN.md`),
koleksi `.txt` lama, maupun file `.epub`. Bookmark per-novel, tema Soft Noir (terang/galam).

## Fitur
- Daftar novel otomatis (mode *indexed* dari `library_index.json`, atau *legacy* scan folder).
- Mendukung multi-folder library (bisa lebih dari 1 folder via `library_roots` di `config.json` atau UI).
- Baca `.txt`, `.md`, dan `.epub` (EPUB di-parse via stdlib — tanpa dependensi berat, aman Termux).
- Toggle "Tampilkan teks asli" untuk chapter yang punya terjemahan + asli.
- Bookmark per-novel (banyak), disimpan in-folder → ikut Resilio Sync.
- Auto-save progres (chapter terakhir dibaca) per novel.
- Pengaturan real-time: ukuran font, jarak baris, indentasi, margin, lebar baca.
- Panel samping collapsible (Koleksi Novel, Daftar Chapter) & Mode Fokus Baca (Zen Mode).
- Tema terang/galam (default terang), kontras lembut "Soft Noir".
- Library root di-set **manual via UI** ATAU via **`config.json`** di direktori app.

## Menjalankan
Prasyarat: Python 3.11+.

```bash
pip install -r requirements.txt
python main.py
```
Buka browser: http://127.0.0.1:3030

### Di Termux
```bash
pkg install python
pip install -r requirements.txt
termux-setup-storage        # agar bisa akses ~/storage
python main.py
```
Set library root via UI (tombol **Set Folder**) ke folder koleksi (mis. `~/storage/downloads/Novel_Library`).
Atau edit `config.json` -> `"library_root": "/path/ke/Novel_Library"` lalu jalankan.

## Menentukan Library Root (dua jalur)
1. **UI:** klik tombol **Set Folder**, masukkan path (bisa dipisah `;` untuk multi-folder). Tersimpan di `device_config.json` (gitignored, override).
2. **File:** edit `config.json` di direktori app:
   ```json
   { "library_roots": ["E:\\Novel_Library", "D:\\Koleksi_Lain"] }
   ```
   (Field `library_root` dan `global_storage_path` juga dikenali, selaras dengan translator.)

Urutan resolusi: `device_config.json` → `config.json` → fallback `./Novel_Library`.

## Format yang Didukung
| Sumber | Cara dibaca | Teks asli |
|--------|-------------|-----------|
| `library_index.json` (translator) | katalog + isi dari `chapters[]` | ya (field `teks_asli`) |
| `Chapter_NN.md` (translator) | parse section "Hasil Terjemahan" / "Teks Asli" | ya |
| `.txt` (legacy) | isi polos, format `**tebal**`/`*miring*` | tidak |
| `.epub` | stdlib zipfile+xml+html.parser, spine order | tidak |

Folder novel bisa berisi campuran `.txt`/`.md`/`.epub`; semua digabung & diurutkan natural-sort.

## Struktur
```
core/      config, paths (resolusi root + safe_join), storage (JSON atomic)
models/    novel, settings (Pydantic)
services/  library (katalog), reader (isi), epub (parser), progress (bookmark)
api/       router_library, router_chapters, router_progress, router_settings
frontend/  index.html + css (theme/layout) + js (api/state/ui-*)
tests/     pytest (storage, paths, library, reader, epub, progress, api)
```

## UI — 10 Heuristik UX Nielsen
1. **Status sistem:** indikator "Memuat…", posisi "3 / 120", toast "Tersimpan".
2. **Dunia nyata:** bahasa Indonesia (Bab, Pengaturan, Tandai), ikon buku & bintang.
3. **Kontrol & kebebasan:** prev/next, batal Set Folder, hapus bookmark dgn konfirmasi, tutup panel, panel collapsible.
4. **Konsisten:** posisi tombol tetap, shortcut keyboard (←/→, T tema, B bookmark, N novel, C chapter, F fokus), selaras gaya translator.
5. **Pencegahan error:** validasi folder sebelum simpan, disable tombol saat loading, konfirmasi hapus.
6. **Pengenalan bukan ingatan:** daftar chapter terlihat, label bookmark bisa diisi, tooltip ikon.
7. **Fleksibel & efisien:** shortcut, panel settings & sidebars bisa disembunyikan, resume otomatis ke chapter terakhir.
8. **Estetika minimalis:** tema Soft Noir, hanya kontrol relevan, whitespace cukup.
9. **Pemulihan error:** pesan jelas ("Folder tidak ditemukan"), bukan kode.
10. **Bantuan:** README + empty-state yang jelaskan cara Set Folder.

## Shortcut Keyboard
- `←` / `→` / `h` / `l` : chapter sebelumnya / berikutnya
- `T` : ganti tema terang / gelap
- `B` : buka panel chapter dibaca (bookmark)
- `M` : beri catatan bookmark chapter aktif
- `N` : buka / tutup panel koleksi novel
- `C` : buka / tutup panel daftar chapter
- `F` : toggle mode fokus baca (layar penuh)
- `P` : buka / tutup pengaturan tampilan
- `S` : buka dialog set folder koleksi
- `Esc` : tutup panel / drawer yang aktif

## Pengembangan & Test
```bash
pip install -r requirements.txt
python -m pytest -q
```
