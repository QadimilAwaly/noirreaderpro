// Entry point: wiring event & inisialisasi aplikasi.
import { state } from "./state.js";
import { api } from "./api.js";
import { loadNovels, setStatus } from "./ui-library.js";
import { openChapter, navigate } from "./ui-reader.js";
import { initSettings, toggleTheme, toggleSettings, closeSettings } from "./ui-settings.js";
import { toggleBookmarks, closeBookmarks, addOrEditBookmark } from "./ui-bookmarks.js";

let toastTimer = null;

export function showToast(msg, type = "info") {
  const t = document.getElementById("toast");
  if (!t) return;

  t.textContent = msg;
  t.className = "toast" + (type ? ` toast-${type}` : "");
  t.hidden = false;
  t.style.opacity = "1";

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    t.style.opacity = "0";
    setTimeout(() => { t.hidden = true; }, 250);
  }, 3200);
}

export async function promptSetFolder() {
  const current = (state.libraryRoots && state.libraryRoots.length)
    ? state.libraryRoots.join("; ")
    : (state.libraryRoot || "");

  const rawPath = prompt(
    "Masukkan path folder koleksi novel.\nBisa lebih dari 1 folder (pisahkan dengan tanda ; atau baris baru):",
    current
  );
  if (rawPath === null) return; // User membatalkan

  const path = rawPath.trim();
  if (!path) {
    showToast("Path folder tidak boleh kosong", "error");
    return;
  }

  setStatus("Menyimpan folder…");
  try {
    const r = await api.post("/api/set-library-root", { path });
    const countNote = (r.library_roots && r.library_roots.length > 1)
      ? ` (${r.library_roots.length} folder)`
      : "";
    showToast(`Pustaka diatur: ${r.novel_count} novel ditemukan${countNote}`, "success");
    await loadNovels();
  } catch (e) {
    showToast(e.message, "error");
    setStatus("Gagal");
  }
}

// Sidebars & Collapsing logic
const sidebarBackdrop = document.getElementById("sidebar-backdrop");

export function toggleNovels(force) {
  if (window.innerWidth <= 980) {
    const isShow = typeof force === "boolean" ? force : !document.body.classList.contains("show-mobile-novels");
    document.body.classList.toggle("show-mobile-novels", isShow);
    if (isShow) document.body.classList.remove("show-mobile-chapters");
    if (sidebarBackdrop) sidebarBackdrop.hidden = !document.body.classList.contains("show-mobile-novels");
  } else {
    const isCollapse = typeof force === "boolean" ? !force : !document.body.classList.contains("collapse-novels");
    document.body.classList.toggle("collapse-novels", isCollapse);
    saveSidebarState();
  }
  updateToggleButtons();
}

export function toggleChapters(force) {
  if (window.innerWidth <= 980) {
    const isShow = typeof force === "boolean" ? force : !document.body.classList.contains("show-mobile-chapters");
    document.body.classList.toggle("show-mobile-chapters", isShow);
    if (isShow) document.body.classList.remove("show-mobile-novels");
    if (sidebarBackdrop) sidebarBackdrop.hidden = !document.body.classList.contains("show-mobile-chapters");
  } else {
    const isCollapse = typeof force === "boolean" ? !force : !document.body.classList.contains("collapse-chapters");
    document.body.classList.toggle("collapse-chapters", isCollapse);
    saveSidebarState();
  }
  updateToggleButtons();
}

export function toggleZenMode() {
  if (window.innerWidth <= 980) {
    closeAllSidebars();
    closeSettings();
    closeBookmarks();
    showToast("Mode Fokus: Layar Penuh", "info");
  } else {
    const isZen = document.body.classList.contains("collapse-novels") && document.body.classList.contains("collapse-chapters");
    if (isZen) {
      document.body.classList.remove("collapse-novels", "collapse-chapters");
      showToast("Panel Samping Ditampilkan", "info");
    } else {
      document.body.classList.add("collapse-novels", "collapse-chapters");
      showToast("Mode Fokus: Layar Penuh (F)", "info");
    }
    updateToggleButtons();
    saveSidebarState();
  }
}

export function closeAllSidebars() {
  document.body.classList.remove("show-mobile-novels", "show-mobile-chapters");
  if (sidebarBackdrop) sidebarBackdrop.hidden = true;
  updateToggleButtons();
}

function updateToggleButtons() {
  const btnNovels = document.getElementById("btn-toggle-novels");
  const btnChapters = document.getElementById("btn-toggle-chapters");
  const btnZen = document.getElementById("btn-zen-mode");

  if (window.innerWidth <= 980) {
    if (btnNovels) btnNovels.classList.toggle("active", document.body.classList.contains("show-mobile-novels"));
    if (btnChapters) btnChapters.classList.toggle("active", document.body.classList.contains("show-mobile-chapters"));
    if (btnZen) btnZen.classList.remove("active");
  } else {
    const novelsOpen = !document.body.classList.contains("collapse-novels");
    const chaptersOpen = !document.body.classList.contains("collapse-chapters");
    if (btnNovels) btnNovels.classList.toggle("active", novelsOpen);
    if (btnChapters) btnChapters.classList.toggle("active", chaptersOpen);
    if (btnZen) btnZen.classList.toggle("active", !novelsOpen && !chaptersOpen);
  }
}

function saveSidebarState() {
  try {
    localStorage.setItem("readerpro_novels_collapse", document.body.classList.contains("collapse-novels") ? "1" : "0");
    localStorage.setItem("readerpro_chapters_collapse", document.body.classList.contains("collapse-chapters") ? "1" : "0");
  } catch {}
}

function restoreSidebarState() {
  if (window.innerWidth > 980) {
    try {
      if (localStorage.getItem("readerpro_novels_collapse") === "1") {
        document.body.classList.add("collapse-novels");
      }
      if (localStorage.getItem("readerpro_chapters_collapse") === "1") {
        document.body.classList.add("collapse-chapters");
      }
    } catch {}
    updateToggleButtons();
  }
}

// Topbar event listeners
const btnToggleNovels = document.getElementById("btn-toggle-novels");
if (btnToggleNovels) btnToggleNovels.onclick = () => toggleNovels();

const btnToggleChapters = document.getElementById("btn-toggle-chapters");
if (btnToggleChapters) btnToggleChapters.onclick = () => toggleChapters();

const btnZenMode = document.getElementById("btn-zen-mode");
if (btnZenMode) btnZenMode.onclick = () => toggleZenMode();

const btnSetFolder = document.getElementById("btn-set-folder");
if (btnSetFolder) btnSetFolder.onclick = () => promptSetFolder();

const btnToggleTheme = document.getElementById("btn-toggle-theme");
if (btnToggleTheme) btnToggleTheme.onclick = () => toggleTheme();

const btnAddBookmark = document.getElementById("btn-add-bookmark");
if (btnAddBookmark) btnAddBookmark.onclick = () => addOrEditBookmark();

// Sidebar header collapse buttons
const btnCollapseNovels = document.getElementById("btn-collapse-novels");
if (btnCollapseNovels) {
  btnCollapseNovels.onclick = () => {
    if (window.innerWidth <= 980) closeAllSidebars();
    else toggleNovels(false);
  };
}

const btnCollapseChapters = document.getElementById("btn-collapse-chapters");
if (btnCollapseChapters) {
  btnCollapseChapters.onclick = () => {
    if (window.innerWidth <= 980) closeAllSidebars();
    else toggleChapters(false);
  };
}

// Reader toolbar quick navigation buttons
const btnReaderNovels = document.getElementById("btn-reader-novels");
if (btnReaderNovels) btnReaderNovels.onclick = () => toggleNovels();

const btnReaderChapters = document.getElementById("btn-reader-chapters");
if (btnReaderChapters) btnReaderChapters.onclick = () => toggleChapters();

// Sidebar backdrop click
if (sidebarBackdrop) {
  sidebarBackdrop.onclick = () => closeAllSidebars();
}

// Drawer backdrop click
const drawerBackdrop = document.getElementById("drawer-backdrop");
if (drawerBackdrop) {
  drawerBackdrop.onclick = () => {
    closeSettings();
    closeBookmarks();
  };
}

// Window resize listener to sync state
window.addEventListener("resize", () => {
  if (window.innerWidth > 980) {
    closeAllSidebars();
    restoreSidebarState();
  } else {
    updateToggleButtons();
  }
});

// Keyboard shortcuts (Nielsen #7: Flexibility & efficiency of use)
document.addEventListener("keydown", (e) => {
  const activeTag = document.activeElement ? document.activeElement.tagName : "";
  if (activeTag === "INPUT" || activeTag === "TEXTAREA" || activeTag === "SELECT") {
    if (e.key === "Escape") {
      document.activeElement.blur();
    }
    return;
  }

  if (e.key === "ArrowLeft" || e.key === "h" || e.key === "H") {
    navigate(-1);
  } else if (e.key === "ArrowRight" || e.key === "l" || e.key === "L") {
    navigate(1);
  } else if (e.key === "t" || e.key === "T") {
    toggleTheme();
  } else if (e.key === "b" || e.key === "B") {
    toggleBookmarks();
  } else if (e.key === "p" || e.key === "P") {
    toggleSettings();
  } else if (e.key === "n" || e.key === "N") {
    toggleNovels();
  } else if (e.key === "c" || e.key === "C") {
    toggleChapters();
  } else if (e.key === "f" || e.key === "F") {
    toggleZenMode();
  } else if (e.key === "s" || e.key === "S") {
    promptSetFolder();
  } else if (e.key === "m" || e.key === "M") {
    addOrEditBookmark();
  } else if (e.key === "Escape") {
    const settingsPanel = document.getElementById("settings-panel");
    const bmPanel = document.getElementById("bookmarks-panel");
    if (settingsPanel && !settingsPanel.hidden) {
      closeSettings();
    } else if (bmPanel && !bmPanel.hidden) {
      closeBookmarks();
    } else if (document.body.classList.contains("show-mobile-novels") || document.body.classList.contains("show-mobile-chapters")) {
      closeAllSidebars();
    }
  }
});

async function init() {
  await initSettings();
  restoreSidebarState();
  await loadNovels();
}

init();
