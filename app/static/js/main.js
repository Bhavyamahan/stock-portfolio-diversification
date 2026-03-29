// ── Auto-dismiss flash alerts after 4 seconds ─────────────────
document.addEventListener("DOMContentLoaded", function () {
  var alerts = document.querySelectorAll(".alert");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = "opacity 0.5s ease";
      alert.style.opacity    = "0";
      setTimeout(function () { alert.remove(); }, 500);
    }, 4000);
  });

  // Apply saved dark mode preference on page load
  var saved = localStorage.getItem("darkMode");
  if (saved === "true") {
    document.documentElement.setAttribute("data-theme", "dark");
    var icon = document.getElementById("darkIcon");
    if (icon) icon.textContent = "☀️";
  }
});

// ── Dark mode toggle ───────────────────────────────────────────
function toggleDark() {
  var html    = document.documentElement;
  var icon    = document.getElementById("darkIcon");
  var isDark  = html.getAttribute("data-theme") === "dark";

  if (isDark) {
    html.setAttribute("data-theme", "light");
    localStorage.setItem("darkMode", "false");
    if (icon) icon.textContent = "🌙";
  } else {
    html.setAttribute("data-theme", "dark");
    localStorage.setItem("darkMode", "true");
    if (icon) icon.textContent = "☀️";
  }
}
