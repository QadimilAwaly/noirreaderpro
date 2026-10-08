// Util bersama — hindari deklarasi ganda antar-modul.
export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
}

let toastTimer = null;

export function showToast(msg, type = "info") {
  const t = document.getElementById("toast");
  if (!t) return;

  t.textContent = msg;
  t.className = `toast toast-${type} show`;
  t.hidden = false;

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    t.className = "toast";
    t.hidden = true;
  }, 2400);
}
