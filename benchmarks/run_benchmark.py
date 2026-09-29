#!/usr/bin/env python3
"""
Benchmark workload for Noir Reader Pro:
Simulates a complete, realistic reading session across multiple novel formats:
- Multi-library root scanning (indexed translator, markdown, plaintext, EPUB)
- Chapter listings with natural sorting
- Chapter text retrieval and parsing
- Progress and bookmark state persistence
- Settings and theme adjustments
"""
import json
import os
import shutil
import sys
import tempfile
import time
import warnings
import zipfile
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def create_fixture_library(base_dir: Path) -> tuple[Path, Path]:
    root1 = base_dir / "lib_indexed"
    root2 = base_dir / "lib_legacy"
    root1.mkdir(parents=True, exist_ok=True)
    root2.mkdir(parents=True, exist_ok=True)

    # 1. Indexed Library with 2 novels (50 chapters and 30 chapters)
    novels_data = [
        {"id": "nov_mysteries", "judul": "Lord of Mysteries", "folder_path": "Lord of Mysteries"},
        {"id": "nov_apotheosis", "judul": "Apotheosis", "folder_path": "Apotheosis"},
    ]
    chapters_data = []
    for i in range(50):
        chapters_data.append({
            "id": f"lom_{i+1}",
            "novel_id": "nov_mysteries",
            "nomor_chapter": i + 1,
            "judul_chapter": f"Chapter {i+1}: The Beginning of Mystery",
            "translation": f"<p>Ini adalah hasil terjemahan bab {i+1}. Paragraf pembuka yang mendalam.</p>" * 5,
            "teks_asli": f"<p>Original chapter {i+1} text. Deep beginning paragraph.</p>" * 5,
        })
    for i in range(30):
        chapters_data.append({
            "id": f"apo_{i+1}",
            "novel_id": "nov_apotheosis",
            "nomor_chapter": i + 1,
            "judul_chapter": f"Bab {i+1}: Kultivasi Surgawi",
            "translation": f"<p>Kultivasi bab {i+1} mencapai tingkat berikutnya.</p>" * 4,
            "teks_asli": f"<p>Cultivation chapter {i+1} achieves next level.</p>" * 4,
        })

    index_file = root1 / "library_index.json"
    index_file.write_text(
        json.dumps({"novels": novels_data, "chapters": chapters_data}, ensure_ascii=False),
        encoding="utf-8",
    )
    (root1 / "Lord of Mysteries").mkdir(exist_ok=True)
    (root1 / "Apotheosis").mkdir(exist_ok=True)

    # 2. Legacy Library with Markdown, Plaintext, and EPUB
    # 2a. Markdown novel (20 chapters)
    md_folder = root2 / "Shadow Slave"
    md_folder.mkdir(exist_ok=True)
    for i in range(1, 21):
        ch_file = md_folder / f"Chapter_{i:02d}.md"
        content = (
            f"# Chapter {i}: Nightmare Spire\n\n"
            f"## Hasil Terjemahan\n\n"
            f"Kekelaman menyelimuti menara mimpi buruk tingkat {i}.\n\n"
            f"**Sunny** menatap bayangan yang menari perlahan di kejauhan.\n\n"
            f"---\n\n"
            f"## Teks Asli\n\n"
            f"Darkness shrouded the nightmare spire at floor {i}.\n\n"
            f"Sunny looked at the shadows dancing slowly in the distance.\n"
        )
        ch_file.write_text(content, encoding="utf-8")

    # 2b. Plaintext novel (20 chapters)
    txt_folder = root2 / "Coiling Dragon"
    txt_folder.mkdir(exist_ok=True)
    for i in range(1, 21):
        ch_file = txt_folder / f"Bab_{i:02d}.txt"
        ch_file.write_text(
            f"Linley melatih jurus bumi di gunung ke-{i}.\n"
            f"Angin berhembus kencang membawa energi sihir elemental.\n" * 6,
            encoding="utf-8",
        )

    # 2c. EPUB novel (15 chapters)
    epub_folder = root2 / "Martial World"
    epub_folder.mkdir(exist_ok=True)
    epub_path = epub_folder / "Martial_World_Vol_1.epub"
    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?>\n'
            '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">\n'
            '  <rootfiles>\n'
            '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
            '  </rootfiles>\n'
            '</container>',
        )
        manifest_items = []
        spine_items = []
        for i in range(1, 16):
            manifest_items.append(f'<item id="ch{i}" href="ch{i}.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append(f'<itemref idref="ch{i}"/>')
            zf.writestr(
                f"OEBPS/ch{i}.xhtml",
                f'<?xml version="1.0" encoding="utf-8"?>\n'
                f'<!DOCTYPE html>\n'
                f'<html xmlns="http://www.w3.org/1999/xhtml">\n'
                f'<head><title>Chapter {i}: Martial Realm</title></head>\n'
                f'<body>\n'
                f'<h2>Chapter {i}: Martial Realm</h2>\n'
                f'<p>Lin Ming stepped into the trial tower realm number {i}.</p>\n'
                f'<p>The thunder and fire energies surged violently around him.</p>\n'
                f'</body>\n'
                f'</html>',
            )

        opf_content = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">\n'
            '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
            '    <dc:title>Martial World Volume 1</dc:title>\n'
            '  </metadata>\n'
            f'  <manifest>\n    {"    ".join(manifest_items)}\n  </manifest>\n'
            f'  <spine>\n    {"    ".join(spine_items)}\n  </spine>\n'
            '</package>'
        )
        zf.writestr("OEBPS/content.opf", opf_content)

    return root1, root2


def run_benchmark():
    temp_dir = Path(tempfile.mkdtemp(prefix="noir_bench_"))
    try:
        root1, root2 = create_fixture_library(temp_dir)
        library_roots = f"{str(root1)};{str(root2)}"
        os.environ["NOIR_LIBRARY_ROOTS"] = library_roots
        os.environ["NOIR_DATA_DIR"] = str(temp_dir)

        # Clear caches before starting
        from services.library import clear_library_cache
        from services.epub import clear_epub_cache
        from services.reader import clear_reader_cache
        clear_library_cache()
        clear_epub_cache()
        clear_reader_cache()

        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Warm-up (1 iteration)
        res = client.get("/api/novels")
        assert res.status_code == 200, f"Warmup failed: {res.text}"
        novels = res.json().get("novels", [])
        assert len(novels) >= 5, f"Expected at least 5 novels, got {len(novels)}"
        for n in novels:
            client.get(f"/api/chapters?novel_id={n['id']}")

        # Timed workload
        total_payload_bytes = 0
        library_times = []
        chapter_times = []
        progress_times = []

        start_cpu = time.process_time()
        start_wall = time.perf_counter()

        ITERATIONS = 5
        for iteration in range(ITERATIONS):
            # 1. Library catalog listing
            t0 = time.perf_counter()
            res = client.get("/api/novels")
            library_times.append(time.perf_counter() - t0)
            total_payload_bytes += len(res.content)
            current_novels = res.json().get("novels", [])

            # 2. Chapter listing for all novels
            novel_chapters_map = {}
            for n in current_novels:
                t0 = time.perf_counter()
                c_res = client.get(f"/api/chapters?novel_id={n['id']}")
                chapter_times.append(time.perf_counter() - t0)
                total_payload_bytes += len(c_res.content)
                novel_chapters_map[n["id"]] = c_res.json().get("chapters", [])

            # 3. Read chapter sequence across novels
            # Read first 5 chapters of each novel
            for n in current_novels:
                chaps = novel_chapters_map.get(n["id"], [])[:5]
                for ch in chaps:
                    t0 = time.perf_counter()
                    r_res = client.get(f"/api/chapter?novel_id={n['id']}&ref={ch['ref']}")
                    chapter_times.append(time.perf_counter() - t0)
                    total_payload_bytes += len(r_res.content)

                    # Mark read
                    t0 = time.perf_counter()
                    p_res = client.post(
                        f"/api/mark-read?novel_id={n['id']}",
                        json={"chapter_index": ch["index"], "label": ch["title"]},
                    )
                    progress_times.append(time.perf_counter() - t0)
                    total_payload_bytes += len(p_res.content)

                # Query progress
                t0 = time.perf_counter()
                prog_res = client.get(f"/api/progress?novel_id={n['id']}")
                progress_times.append(time.perf_counter() - t0)
                total_payload_bytes += len(prog_res.content)

            # 4. Settings roundtrip
            s_res = client.get("/api/settings")
            total_payload_bytes += len(s_res.content)
            s_data = s_res.json()
            s_data["font_size"] = 14 + (iteration % 4)
            s_data["theme"] = "dark" if iteration % 2 == 0 else "light"
            client.post("/api/settings", json=s_data)

        end_wall = time.perf_counter()
        end_cpu = time.process_time()

        total_wall_ms = (end_wall - start_wall) * 1000.0
        total_cpu_ms = (end_cpu - start_cpu) * 1000.0
        lib_ms = sum(library_times) * 1000.0
        chap_ms = sum(chapter_times) * 1000.0
        prog_ms = sum(progress_times) * 1000.0
        payload_kb = total_payload_bytes / 1024.0

        # Output metrics
        print(f"METRIC latency_ms={total_wall_ms:.2f}")
        print(f"METRIC library_latency_ms={lib_ms:.2f}")
        print(f"METRIC chapter_latency_ms={chap_ms:.2f}")
        print(f"METRIC progress_latency_ms={prog_ms:.2f}")
        print(f"METRIC cpu_time_ms={total_cpu_ms:.2f}")
        print(f"METRIC payload_kb={payload_kb:.2f}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_benchmark()
