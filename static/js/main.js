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

// User Session Tracking
let currentSessionId = null;

async function startSession() {
  const metaActivity = document.querySelector('meta[name="activity-name"]');
  const activity = metaActivity ? metaActivity.getAttribute("content") : document.title;
  
  try {
    const res = await postJSON("/api/analytics/session/start", { activity });
    if (res.success && res.session_id) {
      currentSessionId = res.session_id;
    }
  } catch (err) {
    console.error("Failed to start session:", err);
  }
}

function endSession() {
  if (currentSessionId) {
    const data = JSON.stringify({ session_id: currentSessionId });
    // Use sendBeacon for reliable delivery when the page unloads
    const blob = new Blob([data], { type: "application/json" });
    const url = "/api/analytics/session/end";
    
    // We can't easily send custom headers with sendBeacon, so if CSRF is required,
    // we append it to the URL query string.
    const csrfToken = getCsrfToken();
    navigator.sendBeacon(`${url}?csrf_token=${csrfToken}`, blob);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Only start session tracking if user is logged in (has nav-avatar or logout link)
  if (document.querySelector('a[href="/logout"]') || document.querySelector('.nav-avatar')) {
    startSession();
  }
});

window.addEventListener("beforeunload", endSession);
window.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") {
    endSession();
  } else if (document.visibilityState === "visible") {
    // Optionally start a new session when they come back
    startSession();
  }
});
