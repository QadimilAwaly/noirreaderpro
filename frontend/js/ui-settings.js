// Panel pengaturan tampilan + tema + lebar baca.
import { state } from "./state.js";
import { api } from "./api.js";
import { showToast } from "./main.js";

const panel = document.getElementById("settings-panel");
const btnSettings = document.getElementById("btn-settings");
const btnClose = document.getElementById("btn-close-settings");
const backdrop = document.getElementById("drawer-backdrop");

const rngFont = document.getElementById("rng-font");
const rngSpacing = document.getElementById("rng-spacing");
const rngWidth = document.getElementById("rng-width");
const rngIndent = document.getElementById("rng-indent");
const selTheme = document.getElementById("sel-theme");
const valFont = document.getElementById("val-font");
const valSpacing = document.getElementById("val-spacing");
const valWidth = document.getElementById("val-width");
const valIndent = document.getElementById("val-indent");

let pushTimer = null;

export function openSettings() {
  const bmPanel = document.getElementById("bookmarks-panel");
  if (bmPanel) bmPanel.hidden = true;
  const btnBm = document.getElementById("btn-bookmarks");
  if (btnBm) btnBm.setAttribute("aria-expanded", "false");

  panel.hidden = false;
  btnSettings.setAttribute("aria-expanded", "true");
  if (backdrop) backdrop.hidden = false;
}

export function closeSettings() {
  panel.hidden = true;
  btnSettings.setAttribute("aria-expanded", "false");
  const bmPanel = document.getElementById("bookmarks-panel");
  if (backdrop && (!bmPanel || bmPanel.hidden)) {
    backdrop.hidden = true;
  }
}

export function toggleSettings() {
  if (panel.hidden) {
    openSettings();
  } else {
    closeSettings();
  }
}

btnSettings.onclick = () => toggleSettings();
btnClose.onclick = () => closeSettings();

export function applyVars() {
  const r = document.documentElement;
  r.style.setProperty("--font-size", (state.settings.font_size || 16) + "px");
  r.style.setProperty("--line-spacing", String(state.settings.line_spacing || 1.7));
  r.style.setProperty("--para-indent", (state.settings.paragraph_indent ?? 28) + "px");
  r.style.setProperty("--page-margin", (state.settings.page_margin || 24) + "px");
  r.style.setProperty("--read-width", (state.settings.read_width || 720) + "px");
}

export function setThemeClass(theme) {
  document.body.classList.remove("theme-light", "theme-dark");
  document.body.classList.add("theme-" + (theme === "dark" ? "dark" : "light"));
}

export function syncInputs() {
  if (rngFont) rngFont.value = state.settings.font_size || 16;
  if (valFont) valFont.textContent = state.settings.font_size || 16;

  if (rngSpacing) rngSpacing.value = state.settings.line_spacing || 1.7;
  if (valSpacing) valSpacing.textContent = state.settings.line_spacing || 1.7;

  if (rngWidth) rngWidth.value = state.settings.read_width || 720;
  if (valWidth) valWidth.textContent = state.settings.read_width || 720;

  if (rngIndent) rngIndent.value = state.settings.paragraph_indent ?? 28;
  if (valIndent) valIndent.textContent = state.settings.paragraph_indent ?? 28;

  if (selTheme) selTheme.value = state.settings.theme || "light";
  setThemeClass(state.settings.theme || "light");
}

function debouncedPushSettings() {
  clearTimeout(pushTimer);
  pushTimer = setTimeout(async () => {
    try {
      const s = await api.post("/api/settings", state.settings);
      state.settings = { ...state.settings, ...s };
    } catch (e) {
      showToast(e.message, "error");
    }
  }, 250);
}

if (rngFont) {
  rngFont.oninput = () => {
    valFont.textContent = rngFont.value;
    state.settings.font_size = +rngFont.value;
    applyVars();
    debouncedPushSettings();
  };
}

if (rngSpacing) {
  rngSpacing.oninput = () => {
    valSpacing.textContent = rngSpacing.value;
    state.settings.line_spacing = +rngSpacing.value;
    applyVars();
    debouncedPushSettings();
  };
}

if (rngWidth) {
  rngWidth.oninput = () => {
    valWidth.textContent = rngWidth.value;
    state.settings.read_width = +rngWidth.value;
    applyVars();
    debouncedPushSettings();
  };
}

if (rngIndent) {
  rngIndent.oninput = () => {
    valIndent.textContent = rngIndent.value;
    state.settings.paragraph_indent = +rngIndent.value;
    applyVars();
    debouncedPushSettings();
  };
}

if (selTheme) {
  selTheme.onchange = () => {
    state.settings.theme = selTheme.value;
    setThemeClass(selTheme.value);
    debouncedPushSettings();
    api.post(`/api/theme?theme=${selTheme.value}`).catch(() => {});
  };
}

export async function initSettings() {
  try {
    const s = await api.get("/api/settings");
    state.settings = { ...state.settings, ...s };
  } catch (e) {
    // Gunakan nilai default jika backend belum siap
  }
  applyVars();
  syncInputs();
}

export function toggleTheme() {
  state.settings.theme = state.settings.theme === "light" ? "dark" : "light";
  setThemeClass(state.settings.theme);
  if (selTheme) selTheme.value = state.settings.theme;
  api.post(`/api/theme?theme=${state.settings.theme}`).catch(() => {});
  showToast(`Tema: ${state.settings.theme === "dark" ? "Gelap" : "Terang"}`);
}
