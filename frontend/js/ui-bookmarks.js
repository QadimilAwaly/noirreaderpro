// Panel "Chapter Dibaca" (auto-bookmark & manual bookmark).
import { state } from "./state.js";
import { api } from "./api.js";
import { escapeHtml } from "./util.js";
import { openChapter } from "./ui-reader.js";
import { showToast } from "./main.js";

const panel = document.getElementById("bookmarks-panel");
const btnBm = document.getElementById("btn-bookmarks");
const btnClose = document.getElementById("btn-close-bookmarks");
const list = document.getElementById("bookmark-list");
const elCount = document.getElementById("bm-count");
const backdrop = document.getElementById("drawer-backdrop");

export function openBookmarks() {
  const settingsPanel = document.getElementById("settings-panel");
  if (settingsPanel) settingsPanel.hidden = true;
  const btnSettings = document.getElementById("btn-settings");
  if (btnSettings) btnSettings.setAttribute("aria-expanded", "false");

  renderBookmarks();
  panel.hidden = false;
  if (btnBm) btnBm.setAttribute("aria-expanded", "true");
  if (backdrop) backdrop.hidden = false;
}

export function closeBookmarks() {
  panel.hidden = true;
  if (btnBm) btnBm.setAttribute("aria-expanded", "false");
  const settingsPanel = document.getElementById("settings-panel");
  if (backdrop && (!settingsPanel || settingsPanel.hidden)) {
    backdrop.hidden = true;
  }
}

export function toggleBookmarks() {
  if (panel.hidden) {
    openBookmarks();
  } else {
    closeBookmarks();
  }
}

if (btnBm) btnBm.onclick = () => toggleBookmarks();
if (btnClose) btnClose.onclick = () => closeBookmarks();

export function renderBookmarks() {
  const sorted = [...state.bookmarks].sort((a, b) => a.chapter_index - b.chapter_index);
  if (elCount) elCount.textContent = String(sorted.length);
  if (!list) return;

  list.innerHTML = "";
  if (!sorted.length) {
    list.innerHTML = `
      <div class="empty-state">
        <p>Belum ada chapter dibaca.</p>
        <p class="hint">Buka chapter mana saja — otomatis tercatat di sini, atau klik tombol <b>🏷️ Tandai</b> untuk catatan manual.</p>
      </div>`;
    return;
  }

  for (const bm of sorted) {
    const ch = state.chapters[bm.chapter_index];
    const label = bm.label || (ch ? ch.title : `Chapter ${bm.chapter_index + 1}`);
    const isCurrent = ch && ch.ref === state.activeChapterRef;

    const div = document.createElement("div");
    div.className = "bm-item" + (isCurrent ? " active" : "");
    div.setAttribute("role", "button");
    div.setAttribute("tabindex", "0");
    div.innerHTML = `
      <div class="bm-info">
        <div class="bm-label">${escapeHtml(label)}</div>
        <div class="bm-pos">Chapter ${bm.chapter_index + 1}${isCurrent ? ' <span class="tag">Sedang dibaca</span>' : ''}</div>
      </div>
      <button class="bm-del" title="Hapus dari daftar baca" aria-label="Hapus bookmark Chapter ${bm.chapter_index + 1}">🗑</button>
    `;

    div.onclick = (e) => {
      if (e.target.closest(".bm-del")) return;
      if (ch) {
        openChapter(ch.ref);
        closeBookmarks();
      }
    };

    div.onkeydown = (e) => {
      if (e.key === "Enter" || e.key === " ") {
        if (!e.target.closest(".bm-del")) {
          e.preventDefault();
          if (ch) {
            openChapter(ch.ref);
            closeBookmarks();
          }
        }
      }
    };

    const delBtn = div.querySelector(".bm-del");
    delBtn.onclick = async (e) => {
      e.stopPropagation();
      const confirmDelete = confirm(`Hapus "${label}" dari daftar chapter dibaca?`);
      if (!confirmDelete) return;

      try {
        await api.delete(`/api/bookmark?novel_id=${encodeURIComponent(state.activeNovelId)}&bookmark_id=${encodeURIComponent(bm.id)}`);
        state.bookmarks = state.bookmarks.filter(b => b.id !== bm.id);
        state.readSet = new Set(state.bookmarks.map(b => b.chapter_index));
        renderBookmarks();
        const { renderChapterCards } = await import("./ui-reader.js");
        renderChapterCards();
        showToast("Bookmark dihapus");
      } catch (err) {
        showToast(err.message, "error");
      }
    };

    list.appendChild(div);
  }
}

export async function addOrEditBookmark() {
  if (!state.activeNovelId || !state.activeChapterRef) {
    showToast("Pilih chapter terlebih dahulu untuk menandai", "info");
    return;
  }
  const ch = state.chapters.find(c => c.ref === state.activeChapterRef);
  if (!ch) return;

  const existing = state.bookmarks.find(b => b.chapter_index === ch.index);
  const defaultLabel = existing ? existing.label : ch.title;
  const label = prompt("Beri catatan / label bookmark untuk chapter ini:", defaultLabel || `Chapter ${ch.index + 1}`);

  if (label === null) return; // User membatalkan

  try {
    const prog = await api.post(`/api/mark-read?novel_id=${encodeURIComponent(state.activeNovelId)}`, {
      chapter_index: ch.index,
      label: label.trim(),
    });
    state.bookmarks = prog.bookmarks || [];
    state.readSet = new Set(state.bookmarks.map(b => b.chapter_index));
    renderBookmarks();
    const { renderChapterCards } = await import("./ui-reader.js");
    renderChapterCards();
    showToast("Bookmark berhasil disimpan!");
  } catch (e) {
    showToast(e.message, "error");
  }
}
