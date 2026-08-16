// Render daftar novel (kartu) & navigasi ke chapter.
import { state, setActiveNovel } from "./state.js";
import { api } from "./api.js";
import { escapeHtml } from "./util.js";
import { loadChapters } from "./ui-reader.js";
import { showToast } from "./main.js";

const elNovelList = document.getElementById("novel-list");
const elNovelEmpty = document.getElementById("novel-empty");
const elNovelCount = document.getElementById("novel-count");
const elBrandSub = document.getElementById("brand-sub");
const elStatusPill = document.getElementById("status-pill");

export function renderNovels() {
  if (!elNovelList) return;
  elNovelList.innerHTML = "";
  if (elNovelCount) elNovelCount.textContent = String(state.novels.length);

  if (!state.novels.length) {
    if (elNovelEmpty) elNovelEmpty.hidden = false;
    return;
  }
  if (elNovelEmpty) elNovelEmpty.hidden = true;

  for (const n of state.novels) {
    const isActive = n.id === state.activeNovelId;
    const div = document.createElement("div");
    div.className = "novel-card" + (isActive ? " active" : "");
    div.setAttribute("role", "button");
    div.setAttribute("tabindex", "0");
    div.setAttribute("aria-label", `${n.judul}, ${n.chapter_count} chapter`);

    div.innerHTML = `
      <div class="nv-title">${escapeHtml(n.judul)}</div>
      <div class="nv-meta">
        <span>${n.chapter_count} chapter</span>
        ${n.has_original ? '<span class="tag">+ asli</span>' : ""}
      </div>
    `;

    div.onclick = () => selectNovel(n);
    div.onkeydown = (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        selectNovel(n);
      }
    };

    elNovelList.appendChild(div);
  }
}

export async function selectNovel(novel) {
  setActiveNovel(novel);
  try {
    localStorage.setItem("readerpro_last_novel_id", novel.id);
  } catch {}
  renderNovels();

  // On small screens, if called by user click from novel drawer, transition to chapter drawer.
  if (window.innerWidth <= 980 && document.body.classList.contains("show-mobile-novels")) {
    document.body.classList.remove("show-mobile-novels");
    document.body.classList.add("show-mobile-chapters");
    const sidebarBackdrop = document.getElementById("sidebar-backdrop");
    if (sidebarBackdrop) sidebarBackdrop.hidden = false;
  }

  await loadChapters(novel.id);
}

export function setStatus(text) {
  if (!elStatusPill) return;
  elStatusPill.textContent = text;
  elStatusPill.style.opacity = "1";
  clearTimeout(setStatus._t);
  setStatus._t = setTimeout(() => {
    if (elStatusPill) elStatusPill.style.opacity = "0.6";
  }, 2200);
}

export async function loadNovels() {
  setStatus("Memuat koleksi…");
  if (elNovelList && !state.novels.length) {
    elNovelList.innerHTML = `
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Memuat koleksi novel…</p>
      </div>`;
  }

  try {
    const data = await api.get("/api/novels");
    state.libraryRoot = data.library_root || "";
    state.libraryRoots = data.library_roots || (data.library_root ? [data.library_root] : []);
    state.novels = data.novels || [];

    if (elBrandSub) {
      if (state.libraryRoots.length > 1) {
        elBrandSub.textContent = `${state.libraryRoots.length} folder pustaka`;
        elBrandSub.title = state.libraryRoots.join("\n");
      } else if (state.libraryRoots.length === 1) {
        const rootPath = state.libraryRoots[0];
        elBrandSub.textContent = rootPath.split(/[\\/]/).filter(Boolean).pop() || "Pustaka lokal";
        elBrandSub.title = rootPath;
      } else {
        elBrandSub.textContent = "Pustaka lokal";
        elBrandSub.title = "";
      }
    }

    renderNovels();

    if (state.novels.length) {
      const folderNote = state.libraryRoots.length > 1 ? ` · ${state.libraryRoots.length} folder` : "";
      setStatus(`Siap · ${state.novels.length} novel${folderNote}`);

      // Otomatis load last novel yang dibaca (atau novel pertama) di mobile dan desktop
      let targetNovel = null;
      try {
        const lastNovelId = localStorage.getItem("readerpro_last_novel_id");
        if (lastNovelId) {
          targetNovel = state.novels.find(n => n.id === lastNovelId);
        }
      } catch {}

      if (!targetNovel) {
        targetNovel = state.novels[0];
      }

      if (targetNovel) {
        await selectNovel(targetNovel);
      }
    } else {
      if (elNovelEmpty) elNovelEmpty.hidden = false;
      setStatus("Cek config.json");
    }
  } catch (e) {
    if (elNovelEmpty) elNovelEmpty.hidden = false;
    setStatus("Cek config.json");
    showToast(e.message, "error");
  }
}
