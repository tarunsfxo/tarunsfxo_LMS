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

  // ── Notification Dropdown ──
  const navNotifBtn = document.getElementById("navNotifBtn");
  const navNotifDropdown = document.getElementById("navNotifDropdown");
  const navNotifDot = document.getElementById("navNotifDot");
  const navNotifList = document.getElementById("navNotifList");
  const navNotifClear = document.getElementById("navNotifClear");

  if (navNotifBtn && navNotifDropdown) {
    navNotifBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      navNotifDropdown.classList.toggle("show");
      // Load notifications when dropdown is opened
      if (navNotifDropdown.classList.contains("show")) {
        loadNotifications();
      }
    });

    document.addEventListener("click", (e) => {
      if (!navNotifDropdown.contains(e.target) && e.target !== navNotifBtn) {
        navNotifDropdown.classList.remove("show");
      }
    });

    navNotifClear.addEventListener("click", () => {
      const csrfToken = getCsrfToken();
      fetch('/api/analytics/gamification/notifications/read-all', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          loadNotifications();
        }
      });
    });
  }

  function loadNotifications() {
    fetch('/api/analytics/gamification/dashboard')
      .then(res => res.json())
      .then(data => {
        const notifs = data.all_notifications || [];
        if (notifs.length === 0) {
          navNotifList.innerHTML = '<div class="nav-notif-empty">🎉 You\'re all caught up!</div>';
          navNotifDot.style.display = "none";
          navNotifClear.style.display = "none";
          return;
        }

        let unreadCount = 0;
        let html = '';
        notifs.forEach(n => {
          if (!n.is_read) unreadCount++;
          let icon = '🔔';
          if (n.type === 'level_up') icon = '🏆';
          else if (n.type === 'badge') icon = '🏅';
          else if (n.type === 'achievement') icon = '🌟';

          html += `
            <div class="nav-notif-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
              <div class="nav-notif-icon">${icon}</div>
              <div class="nav-notif-body">
                <div class="nav-notif-title">${n.title}</div>
                <div class="nav-notif-msg">${n.message}</div>
              </div>
            </div>
          `;
        });

        navNotifList.innerHTML = html;
        navNotifDot.style.display = unreadCount > 0 ? "block" : "none";
        navNotifClear.style.display = unreadCount > 0 ? "block" : "none";

        // Add click events to individual notifications to mark them as read
        navNotifList.querySelectorAll(".nav-notif-item").forEach(item => {
          item.addEventListener("click", () => {
            const id = item.getAttribute("data-id");
            if (item.classList.contains("unread")) {
              const csrfToken = getCsrfToken();
              fetch(`/api/analytics/gamification/notifications/${id}/read`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken }
              })
              .then(() => {
                item.classList.remove("unread");
                loadNotifications(); // Reload to update header & dot
              });
            }
          });
        });
      })
      .catch(err => console.error("Error loading notifications:", err));
  }

  // Pre-load notification state initially (to show/hide red dot)
  if (navNotifBtn) {
    fetch('/api/analytics/gamification/dashboard')
      .then(res => res.json())
      .then(data => {
        const notifs = data.all_notifications || [];
        const hasUnread = notifs.some(n => !n.is_read);
        if (navNotifDot) {
          navNotifDot.style.display = hasUnread ? "block" : "none";
        }
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

  // Remove page-leaving class when page is shown (handles history/back-forward navigation)
  window.addEventListener('pageshow', () => {
    document.body.classList.remove('page-leaving');
  });

  // Page leave transition (fade out)
  document.querySelectorAll('a:not([target="_blank"])').forEach(link => {
    link.addEventListener('click', (e) => {
      // Check if same domain relative link, and not a hash link
      if (link.href && !link.href.startsWith('#') && link.host === window.location.host && !link.href.includes('/logout')) {
        // Allow ctrl/cmd clicks to open in new tab normally
        if (e.metaKey || e.ctrlKey) return;
        e.preventDefault();
        document.body.classList.add('page-leaving');
        setTimeout(() => window.location = link.href, 180);
      }
    });
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

  // Admin Sidebar mobile drawer toggle
  const adminMenuToggle = document.getElementById("adminMenuToggle");
  const adminSidebar = document.getElementById("adminSidebar");
  const adminSidebarOverlay = document.getElementById("adminSidebarOverlay");

  if (adminMenuToggle && adminSidebar && adminSidebarOverlay) {
    adminMenuToggle.addEventListener("click", () => {
      adminSidebar.classList.toggle("open");
      adminSidebarOverlay.classList.toggle("show");
    });

    adminSidebarOverlay.addEventListener("click", () => {
      adminSidebar.classList.remove("open");
      adminSidebarOverlay.classList.remove("show");
    });
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
  }, 6000);
}

// ─── AI Copilot & Command Palette Client ───
document.addEventListener("DOMContentLoaded", () => {
  const copilotTrigger = document.getElementById("ai-copilot-trigger");
  const copilotSidebar = document.getElementById("ai-copilot-sidebar");
  const copilotClose = document.getElementById("ai-copilot-close");
  const copilotForm = document.getElementById("copilotForm");
  const copilotInput = document.getElementById("copilotInput");
  const copilotMessages = document.getElementById("copilotMessages");
  const copilotTyping = document.getElementById("copilotTyping");
  const copilotTypingText = document.getElementById("copilotTypingText");

  // Toggle Sidebar
  if (copilotTrigger && copilotSidebar) {
    copilotTrigger.addEventListener("click", () => {
      copilotSidebar.classList.toggle("open");
      const isOpen = copilotSidebar.classList.contains("open");
      copilotSidebar.setAttribute("aria-hidden", !isOpen);
      if (isOpen && copilotInput) {
        copilotInput.focus();
      }
    });
  }

  if (copilotClose && copilotSidebar) {
    copilotClose.addEventListener("click", () => {
      copilotSidebar.classList.remove("open");
      copilotSidebar.setAttribute("aria-hidden", "true");
    });
  }

  // Handle Question Submission
  window.submitCopilotQuestion = async function(event) {
    if (event) event.preventDefault();
    if (!copilotInput) return false;

    const question = copilotInput.value.trim();
    if (!question) return false;

    copilotInput.value = "";
    appendMessage(question, "user");
    showTyping("Thinking...");

    try {
      // Gather active page context
      const pageContext = {
        url: window.location.pathname,
        title: document.title,
        lesson_content: document.querySelector("main") ? document.querySelector("main").innerText.substring(0, 1500) : "",
        editor_code: window.editor ? window.editor.getValue() : ""
      };

      const response = await fetch("/n8n/ai-mentor/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question, context: pageContext })
      });

      const data = await response.json();
      hideTyping();

      if (data.error) {
        appendMessage(`⚠️ Error: ${data.error}`, "bot");
      } else {
        appendMessage(data.answer, "bot", data.source, data.response_time_ms);
      }
    } catch (err) {
      hideTyping();
      appendMessage("⚠️ Connection error. Please try again later.", "bot");
    }

    return false;
  };

  // Trigger Copilot Predefined Actions
  window.triggerCopilotAction = function(actionType) {
    if (!copilotSidebar.classList.contains("open")) {
      copilotSidebar.classList.add("open");
    }

    let prompt = "";
    switch(actionType) {
      case "ask":
        if (copilotInput) copilotInput.focus();
        return;
      case "explain":
        prompt = `Summarize and explain the key concepts of the current page ("${document.title}").`;
        break;
      case "debug":
        const code = window.editor ? window.editor.getValue() : "";
        if (code) {
          prompt = `Debug and review this code:\n\n\`\`\`\n${code}\n\`\`\``;
        } else {
          prompt = "Explain how to debug common Python and JavaScript syntax errors.";
        }
        break;
      case "quiz":
        prompt = `Generate a quick 3-question quiz (with explanations) based on: "${document.title}".`;
        break;
      case "study_plan":
        prompt = "Create a customized daily study plan recommendation for me based on my active progress.";
        break;
      case "progress":
        prompt = "Give me learning progress insights, my strongest skills, and predicted completion goals.";
        break;
      case "career":
        prompt = "Provide career guidance and show me the developer skill tree roadmap.";
        break;
    }

    if (copilotInput) {
      copilotInput.value = prompt;
      submitCopilotQuestion();
    }
  };

  function appendMessage(text, sender, source = null, responseTime = null) {
    if (!copilotMessages) return;

    const bubble = document.createElement("div");
    bubble.className = `copilot-bubble copilot-${sender}`;

    let bodyHTML = `<div class="copilot-bubble-body">${text.replace(/\n/g, "<br>")}</div>`;

    if (sender === "bot") {
      let metaHTML = "";
      if (source) {
        let label = "AI Answer";
        let tagClass = "ai";
        if (source === "course_notes" || source === "cached_answer" || source === "quiz_notes") {
          label = "Local Knowledge";
          tagClass = "local";
        }
        metaHTML = `<span class="source-tag ${tagClass}">${label}</span>`;
      }
      if (responseTime) {
        metaHTML += ` <span style="font-size:0.7rem;color:rgba(255,255,255,0.3);">${responseTime}ms</span>`;
      }

      if (metaHTML) {
        bodyHTML += `<div class="copilot-meta-row">${metaHTML}</div>`;
      }
    }

    bubble.innerHTML = bodyHTML;
    copilotMessages.appendChild(bubble);
    copilotMessages.scrollTop = copilotMessages.scrollHeight;
  }

  function showTyping(msg = "Thinking...") {
    if (copilotTyping && copilotTypingText) {
      copilotTypingText.textContent = msg;
      copilotTyping.style.display = "flex";
      copilotMessages.scrollTop = copilotMessages.scrollHeight;
    }
  }

  function hideTyping() {
    if (copilotTyping) {
      copilotTyping.style.display = "none";
    }
  }

  // ─── Command Palette (Ctrl + K) ───
  const palette = document.getElementById("command-palette");
  const paletteInput = document.getElementById("command-palette-input");
  const paletteResults = document.getElementById("command-palette-results");
  let selectedIndex = 0;
  let items = [];

  const COMMANDS = [
    { icon: "✨", label: "Ask AI Copilot", action: () => triggerCopilotAction("ask") },
    { icon: "📚", label: "Explain Current Lesson", action: () => triggerCopilotAction("explain") },
    { icon: "💻", label: "Debug Active Code", action: () => triggerCopilotAction("debug") },
    { icon: "📝", label: "Generate Dynamic Quiz", action: () => triggerCopilotAction("quiz") },
    { icon: "🎯", label: "Create Study Plan", action: () => triggerCopilotAction("study_plan") },
    { icon: "📈", label: "Show My Progress Insights", action: () => triggerCopilotAction("progress") },
    { icon: "💼", label: "Get AI Career Advice", action: () => triggerCopilotAction("career") },
    { icon: "🏠", label: "Go to Dashboard", path: "/" },
    { icon: "📖", label: "Browse Bites (Lessons)", path: "/bites" },
    { icon: "🎓", label: "Explore Courses", path: "/courses" },
    { icon: "🏆", label: "View Leaderboard", path: "/leaderboard" },
    { icon: "💻", label: "Coding Practice Workspace", path: "/coding" },
    { icon: "🏷️", label: "View Pricing Plans", path: "/pricing" }
  ];

  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      togglePalette();
    }
  });

  if (palette) {
    palette.addEventListener("click", (e) => {
      if (e.target === palette) togglePalette();
    });
  }

  function togglePalette() {
    if (!palette) return;
    const isHidden = palette.style.display === "none";
    palette.style.display = isHidden ? "flex" : "none";
    palette.setAttribute("aria-hidden", !isHidden);

    if (isHidden && paletteInput) {
      paletteInput.value = "";
      paletteInput.focus();
      renderResults(COMMANDS);
    }
  }

  if (paletteInput) {
    paletteInput.addEventListener("input", () => {
      const q = paletteInput.value.toLowerCase().trim();
      const filtered = COMMANDS.filter(cmd => cmd.label.toLowerCase().includes(q));
      renderResults(filtered);
    });

    paletteInput.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        togglePalette();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        moveSelection(1);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        moveSelection(-1);
      } else if (e.key === "Enter") {
        e.preventDefault();
        triggerSelected();
      }
    });
  }

  function renderResults(filteredItems) {
    if (!paletteResults) return;
    items = filteredItems;
    selectedIndex = 0;

    if (items.length === 0) {
      paletteResults.innerHTML = '<div class="muted" style="padding:16px;text-align:center;font-size:0.88rem;">No results found</div>';
      return;
    }

    paletteResults.innerHTML = items.map((item, idx) => `
      <div class="command-item ${idx === 0 ? 'selected' : ''}" data-index="${idx}">
        <div class="command-item-label">
          <span class="command-item-icon">${item.icon}</span>
          <span>${item.label}</span>
        </div>
        <span class="command-item-shortcut">${item.path ? 'Go to' : 'Action'}</span>
      </div>
    `).join("");

    // Click trigger
    paletteResults.querySelectorAll(".command-item").forEach(el => {
      el.addEventListener("click", () => {
        selectedIndex = parseInt(el.getAttribute("data-index"));
        triggerSelected();
      });
    });
  }

  function moveSelection(dir) {
    if (items.length === 0) return;
    selectedIndex = (selectedIndex + dir + items.length) % items.length;

    paletteResults.querySelectorAll(".command-item").forEach(el => {
      const idx = parseInt(el.getAttribute("data-index"));
      el.classList.toggle("selected", idx === selectedIndex);
    });

    const activeEl = paletteResults.querySelector(".command-item.selected");
    if (activeEl) {
      activeEl.scrollIntoView({ block: "nearest" });
    }
  }

  function triggerSelected() {
    const item = items[selectedIndex];
    if (!item) return;

    togglePalette();

    if (item.action) {
      item.action();
    } else if (item.path) {
      window.location.href = item.path;
    }
  }
});

