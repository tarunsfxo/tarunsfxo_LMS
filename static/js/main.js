// tarunsfxo LMS global JS

document.addEventListener("DOMContentLoaded", () => {
  const navToggle = document.getElementById("navToggle");
  const navLinks = document.getElementById("navLinks");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => navLinks.classList.toggle("open"));
  }

  // Auto-dismiss flash messages after 5s
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });
});

// Read CSRF token from meta tag (injected by Flask-WTF)
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
}

// Shared fetch helpers used across pages
// JSON body POST (quiz submission etc.) — sends CSRF token in header
async function postJSON(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify(data || {}),
  });
  return res.json();
}

// Form-encoded POST (complete-bite endpoint) — sends CSRF token in header
async function postForm(url) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "X-CSRFToken": getCsrfToken() },
  });
  return res.json();
}
