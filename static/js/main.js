// tarunsfxo LMS global JS

document.addEventListener("DOMContentLoaded", () => {
  const threeDotBtn = document.getElementById("threeDotBtn");
  const dropdownMenuContent = document.getElementById("dropdownMenuContent");
  if (threeDotBtn && dropdownMenuContent) {
    threeDotBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdownMenuContent.classList.toggle("show");
    });
    document.addEventListener("click", () => {
      dropdownMenuContent.classList.remove("show");
    });
  }

  // Auto-dismiss flash messages after 5s
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  // Intersection Observer for scroll animations
  const animateElements = document.querySelectorAll(".animate-on-scroll");
  if (animateElements.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px"
    });

    animateElements.forEach((el) => observer.observe(el));
  }
  checkGamificationNotifications();
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

// ─── Gamification Notifications ───
function checkGamificationNotifications() {
  if (!document.querySelector('a[href="/logout"]') && !document.querySelector('.nav-avatar')) {
    return;
  }
  fetch('/api/analytics/gamification/dashboard')
    .then(res => res.json())
    .then(data => {
      if (data.notifications && data.notifications.length > 0) {
        data.notifications.forEach((n, index) => {
          setTimeout(() => {
            showGamificationToast(n.id, n.title, n.message, n.type);
          }, index * 800);
        });
      }
    })
    .catch(err => console.error("Error loading gamification alerts:", err));
}

function showGamificationToast(id, title, message, type) {
  const toast = document.createElement('div');
  
  let bg = 'linear-gradient(135deg, #1e293b, #0f172a)';
  let border = '1px solid rgba(255,255,255,0.15)';
  let icon = '🔔';
  if (type === 'level_up') {
    bg = 'linear-gradient(135deg, #1b3a4b, #0c1f2b)';
    border = '1px solid var(--primary)';
    icon = '🏆';
  } else if (type === 'badge') {
    bg = 'linear-gradient(135deg, #2e1065, #1e1b4b)';
    border = '1px solid #c084fc';
    icon = '🏅';
  } else if (type === 'achievement') {
    bg = 'linear-gradient(135deg, #713f12, #451a03)';
    border = '1px solid #fbbf24';
    icon = '🌟';
  }

  toast.style.position = 'fixed';
  toast.style.bottom = '24px';
  toast.style.right = '24px';
  toast.style.background = bg;
  toast.style.border = border;
  toast.style.color = '#ffffff';
  toast.style.padding = '18px 24px';
  toast.style.borderRadius = '14px';
  toast.style.boxShadow = '0 20px 40px rgba(0,0,0,0.3)';
  toast.style.zIndex = '99999';
  toast.style.display = 'flex';
  toast.style.alignItems = 'center';
  toast.style.gap = '14px';
  toast.style.maxWidth = '360px';
  toast.style.transform = 'translateY(100px)';
  toast.style.opacity = '0';
  toast.style.transition = 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)';

  toast.innerHTML = `
    <div style="font-size:2.2rem;">${icon}</div>
    <div>
      <strong style="display:block;font-size:0.95rem;margin-bottom:2px;color:#ffffff;line-height:1.2;">${title}</strong>
      <span style="font-size:0.82rem;color:rgba(255,255,255,0.85);">${message}</span>
    </div>
  `;

  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.transform = 'translateY(0)';
    toast.style.opacity = '1';
  }, 100);

  setTimeout(() => {
    toast.style.transform = 'translateY(100px)';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 400);
    
    const csrfToken = getCsrfToken();
    fetch(`/api/analytics/gamification/notifications/${id}/read`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken }
    });
  }, 6000);
}
