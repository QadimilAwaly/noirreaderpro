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

let chapterSearchDebounce = null;
if (elSearch) {
  elSearch.oninput = () => {
    clearTimeout(chapterSearchDebounce);
    chapterSearchDebounce = setTimeout(() => {
      state.chapterFilter = elSearch.value.trim().toLowerCase();
      renderChapterCards();
    }, 100);
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

    // Resume chapter yang tepat:
    // 1. Gunakan current_index dari server jika valid
    // 2. Jika current_index bernilai 0 tapi ada riwayat bookmark tersimpan, gunakan bookmark terakhir
    let lastIdx = data.current_index ?? 0;
    if (lastIdx === 0 && state.bookmarks && state.bookmarks.length > 0) {
      const sortedBm = [...state.bookmarks].sort((a, b) => a.chapter_index - b.chapter_index);
      const highestBm = sortedBm[sortedBm.length - 1].chapter_index;
      if (highestBm > 0) {
        lastIdx = highestBm;
      }
    }
    const last = state.chapters.find(c => c.index === lastIdx) || state.chapters[lastIdx] || state.chapters[0];
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
const _chapterCache = new Map();
const MAX_CACHED_CHAPTERS = 25;

function getCachedChapter(novelId, ref) {
  return _chapterCache.get(`${novelId}:${ref}`);
}

function setCachedChapter(novelId, ref, data) {
  const key = `${novelId}:${ref}`;
  if (_chapterCache.size >= MAX_CACHED_CHAPTERS) {
    const oldestKey = _chapterCache.keys().next().value;
    _chapterCache.delete(oldestKey);
  }
  _chapterCache.set(key, data);
}


export function updateActiveChapterCard() {
  if (!elChapterList) return;
  const prevActive = elChapterList.querySelector(".chap-card.active");
  if (prevActive) {
    prevActive.classList.remove("active");
  }
  const currentCh = state.chapters.find(c => c.ref === state.activeChapterRef);
  if (currentCh) {
    const cardEl = document.getElementById(`chap-card-${currentCh.index}`);
    if (cardEl) {
      cardEl.classList.add("active");
      const readIndicator = cardEl.querySelector(".chap-read");
      if (readIndicator && state.readSet.has(currentCh.index)) {
        readIndicator.className = "chap-read";
        readIndicator.textContent = "✓";
        readIndicator.title = "Sudah dibaca";
      }
      cardEl.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
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
  if (elChapterList && elChapterList.children.length === state.chapters.length && !state.chapterFilter) {
    updateActiveChapterCard();
  } else {
    renderChapterCards();
  }

  // Periksa cache chapter di client untuk transisi instan
  const cached = getCachedChapter(novelId, ref);
  if (cached) {
    state.currentChapterData = cached;
    renderContent(cached);
    applyChapterUI(cached);
    recordReadStatus(ch);
    // Sinkronisasi status progres ke server saat membuka chapter dari cache
    api.post(`/api/mark-read?novel_id=${encodeURIComponent(novelId)}`, {
      chapter_index: ch.index,
      label: ch.title || `Chapter ${ch.index + 1}`,
    }).catch(() => {});
    return;
  }

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
    setCachedChapter(novelId, ref, data);
    renderContent(data);
    applyChapterUI(data);
    recordReadStatus(ch);
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

function applyChapterUI(data) {
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
}

function recordReadStatus(ch) {
  if (!state.readSet.has(ch.index)) {
    state.readSet.add(ch.index);
    const exists = state.bookmarks.some(b => b.chapter_index === ch.index);
    if (!exists) {
      state.bookmarks.push({
        id: `bm_auto_${ch.index}`,
        chapter_index: ch.index,
        label: ch.title,
        created_at: new Date().toISOString(),
      });
    }
    updateActiveChapterCard();
    renderBookmarks();
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
