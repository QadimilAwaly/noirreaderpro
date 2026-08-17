// Render isi chapter + navigasi + toggle asli + auto-bookmark saat dibuka.
import { state } from "./state.js";
import { api } from "./api.js";
import { escapeHtml } from "./util.js";
import { setStatus } from "./ui-library.js";
import { renderBookmarks } from "./ui-bookmarks.js";
import { showToast } from "./main.js";

const elContent = document.getElementById("reader-content");
const elToolbar = document.getElementById("reader-toolbar");
const elPos = document.getElementById("reader-pos");
const elPrev = document.getElementById("btn-prev");
const elNext = document.getElementById("btn-next");
const elChkOriginal = document.getElementById("chk-original");
const elOrigWrap = document.getElementById("orig-toggle-wrap");
const elChapterList = document.getElementById("chapter-list");
const elSearch = document.getElementById("chapter-search");
const elChapterTitle = document.getElementById("chapter-novel-title");
const elChapterCount = document.getElementById("chapter-count");
const elClearSearch = document.getElementById("btn-clear-search");
const elSearchInfo = document.getElementById("chapter-search-info");

if (elPrev) elPrev.onclick = () => navigate(-1);
if (elNext) elNext.onclick = () => navigate(1);

if (elChkOriginal) {
  elChkOriginal.onchange = () => {
    state.showOriginal = elChkOriginal.checked;
    if (state.currentChapterData) {
      renderContent(state.currentChapterData);
    } else if (state.activeChapterRef) {
      openChapter(state.activeChapterRef, true);
    }
  };
}

if (elSearch) {
  elSearch.oninput = () => {
    state.chapterFilter = elSearch.value.trim().toLowerCase();
    renderChapterCards();
  };
}

if (elClearSearch) {
  elClearSearch.onclick = () => {
    if (elSearch) elSearch.value = "";
    state.chapterFilter = "";
    renderChapterCards();
    if (elSearch) elSearch.focus();
  };
}

export async function loadChapters(novelId) {
  if (novelId) {
    state.activeNovelId = novelId;
  }
  setStatus("Memuat chapter…");
  if (elChapterTitle) elChapterTitle.textContent = state.activeNovelTitle || "Chapter";
  if (elChapterList) {
    elChapterList.innerHTML = `
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Memuat daftar chapter…</p>
      </div>`;
  }

  try {
    const data = await api.get(`/api/chapters?novel_id=${encodeURIComponent(novelId)}`);
    state.chapters = data.chapters || [];
    state.bookmarks = data.bookmarks || [];
    state.readSet = new Set(state.bookmarks.map(b => b.chapter_index));

    if (elChapterCount) elChapterCount.textContent = String(state.chapters.length);
    renderChapterCards();
    renderBookmarks();

    const lastIdx = data.current_index || 0;
    const last = state.chapters[lastIdx] || state.chapters[0];
    if (last) {
      await openChapter(last.ref, true);
    } else {
      if (elContent) {
        elContent.innerHTML = `
          <div class="reader-placeholder">
            <div class="ph-icon">📭</div>
            <p>Novel ini belum memiliki chapter.</p>
          </div>`;
      }
      if (elToolbar) elToolbar.hidden = true;
    }
    setStatus("Siap");
  } catch (e) {
    if (elChapterList) {
      elChapterList.innerHTML = `
        <div class="empty-state">
          <p>Gagal memuat chapter.</p>
          <p class="hint">${escapeHtml(e.message)}</p>
        </div>`;
    }
    showToast(e.message, "error");
    setStatus("Gagal");
  }
}

export function renderChapterCards() {
  if (!elChapterList) return;
  elChapterList.innerHTML = "";

  const q = state.chapterFilter;
  const filtered = q
    ? state.chapters.filter(c => c.title.toLowerCase().includes(q) || String(c.index + 1).includes(q))
    : state.chapters;

  if (elClearSearch) elClearSearch.hidden = !q;
  if (elSearchInfo) {
    if (q) {
      elSearchInfo.hidden = false;
      elSearchInfo.textContent = `${filtered.length} chapter ditemukan`;
    } else {
      elSearchInfo.hidden = true;
    }
  }

  if (!filtered.length) {
    elChapterList.innerHTML = `
      <div class="empty-state">
        <p>Tidak ada chapter yang cocok.</p>
        <p class="hint">Coba kata kunci pencarian yang lain.</p>
      </div>`;
    return;
  }

  for (const c of filtered) {
    const read = state.readSet.has(c.index);
    const isActive = c.ref === state.activeChapterRef;
    const div = document.createElement("div");
    div.className = "chap-card" + (isActive ? " active" : "");
    div.id = `chap-card-${c.index}`;
    div.setAttribute("role", "button");
    div.setAttribute("tabindex", "0");
    div.setAttribute("aria-label", `Chapter ${c.index + 1}: ${c.title}, ${read ? "sudah dibaca" : "belum dibaca"}`);

    div.innerHTML = `
      <div class="chap-idx">${c.index + 1}</div>
      <div class="chap-title">${escapeHtml(c.title)}</div>
      <div class="chap-read ${read ? "" : "unread"}" title="${read ? "Sudah dibaca" : "Belum dibaca"}">${read ? "✓" : "○"}</div>
    `;

    div.onclick = () => {
      openChapter(c.ref);
      if (window.innerWidth <= 980) {
        document.body.classList.remove("show-mobile-novels", "show-mobile-chapters");
        const sidebarBackdrop = document.getElementById("sidebar-backdrop");
        if (sidebarBackdrop) sidebarBackdrop.hidden = true;
      }
    };

    div.onkeydown = (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        div.click();
      }
    };

    elChapterList.appendChild(div);
  }

  // Scroll active chapter into view smoothly if present
  const activeEl = elChapterList.querySelector(".chap-card.active");
  if (activeEl) {
    activeEl.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
}

export async function openChapter(ref, isResume = false) {
  const ch = state.chapters.find(c => c.ref === ref);
  if (!ch) return;

  const novelId = ch.novel_id || state.activeNovelId;
  if (novelId) {
    state.activeNovelId = novelId;
  }

  state.activeChapterRef = ref;
  renderChapterCards();
  setStatus("Memuat…");

  if (elContent) {
    elContent.innerHTML = `
      <div class="reader-loading">
        <div class="spinner"></div>
        <p>Memuat Chapter ${ch.index + 1}…</p>
      </div>`;
  }

  try {
    const data = await api.get(`/api/chapter?novel_id=${encodeURIComponent(novelId)}&ref=${encodeURIComponent(ref)}`);
    state.currentChapterData = data;

    renderContent(data);

    if (elPos) elPos.textContent = `${data.index + 1} / ${data.total}`;
    if (elToolbar) elToolbar.hidden = false;

    // Boundary button states (disable at first/last chapter)
    if (elPrev) {
      elPrev.disabled = data.index <= 0;
      elPrev.setAttribute("aria-disabled", String(data.index <= 0));
    }
    if (elNext) {
      elNext.disabled = data.index >= data.total - 1;
      elNext.setAttribute("aria-disabled", String(data.index >= data.total - 1));
    }

    if (elOrigWrap) elOrigWrap.style.display = data.original ? "" : "none";
    if (elChkOriginal) {
      elChkOriginal.disabled = !data.original;
      if (data.original) elChkOriginal.checked = state.showOriginal;
    }

    if (elContent) elContent.scrollTop = 0;
    setStatus("Siap");

    // AUTO-BOOKMARK: catat chapter ini sebagai dibaca
    await markRead(ch);
  } catch (e) {
    if (elContent) {
      elContent.innerHTML = `
        <div class="empty-state">
          <p>Gagal memuat isi chapter.</p>
          <p class="hint">${escapeHtml(e.message)}</p>
        </div>`;
    }
    showToast(e.message, "error");
    setStatus("Gagal");
  }
}

async function markRead(ch) {
  const novelId = ch.novel_id || state.activeNovelId;
  if (!novelId) return;

  try {
    const prog = await api.post(
      `/api/mark-read?novel_id=${encodeURIComponent(novelId)}`,
      { chapter_index: ch.index, label: ch.title }
    );
    state.bookmarks = prog.bookmarks || [];
    state.readSet = new Set(state.bookmarks.map(b => b.chapter_index));
    renderChapterCards();
    renderBookmarks();
  } catch (e) {
    // Non-critical, ignore
  }
}

function renderContent(data) {
  if (!elContent) return;
  let html = `<div class="reader-content-inner"><h2 class="chapter-title">${escapeHtml(data.title)}</h2>`;
  html += `<div class="translation">${data.translation}</div>`;
  if (state.showOriginal && data.original) {
    html += `<div class="original-block"><h4>Teks Asli</h4>${data.original}</div>`;
  }
  html += "</div>";
  elContent.innerHTML = html;
}

export function navigate(dir) {
  const idx = state.chapters.findIndex(c => c.ref === state.activeChapterRef);
  if (idx < 0) return;
  const next = idx + dir;
  if (next < 0 || next >= state.chapters.length) return;
  openChapter(state.chapters[next].ref);
}
