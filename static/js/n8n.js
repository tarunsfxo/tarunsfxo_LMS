/**
 * n8n.js — Client-side logic for automation pages
 * =================================================
 * Handles: workflow toggles, AI Mentor chat, Study Planner,
 * Automation Builder, career generation, feedback form.
 */

// ── Workflow Toggle ──────────────────────────────
function toggleWorkflow(el) {
  const id = el.dataset.workflowId;
  fetch(`/n8n/api/workflows/${id}/toggle`, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
    .then(r => r.json())
    .then(data => {
      el.checked = data.is_enabled;
    })
    .catch(() => { el.checked = !el.checked; });
}

// ── AI Mentor Chat ──────────────────────────────
function submitQuestion(e) {
  e.preventDefault();
  const input = document.getElementById('questionInput');
  const q = input.value.trim();
  if (!q) return false;

  // Add user message
  appendChatBubble(q, 'user');
  input.value = '';
  input.disabled = true;
  document.getElementById('sendBtn').disabled = true;

  // Show typing
  document.getElementById('typingIndicator').style.display = 'flex';

  fetch('/n8n/ai-mentor/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: q }),
  })
  .then(r => r.json())
  .then(data => {
    document.getElementById('typingIndicator').style.display = 'none';
    if (data.error) {
      appendChatBubble(data.error, 'bot', 'fallback', 0);
    } else {
      appendChatBubble(data.answer, 'bot', data.source, data.response_time_ms);
    }
    input.disabled = false;
    document.getElementById('sendBtn').disabled = false;
    input.focus();
  })
  .catch(err => {
    document.getElementById('typingIndicator').style.display = 'none';
    appendChatBubble('Something went wrong. Please try again.', 'bot', 'fallback', 0);
    input.disabled = false;
    document.getElementById('sendBtn').disabled = false;
  });

  return false;
}

function appendChatBubble(text, role, source, responseTime) {
  const container = document.getElementById('chatMessages');
  // Remove welcome screen
  const welcome = container.querySelector('.n8n-chat-welcome');
  if (welcome) welcome.remove();

  const bubble = document.createElement('div');
  bubble.className = `n8n-chat-bubble n8n-chat-${role}`;

  if (role === 'user') {
    bubble.innerHTML = `<div class="n8n-chat-content">${escapeHtml(text)}</div>`;
  } else {
    const sourceLabels = {
      course_notes: { badge: 'n8n-source-local', label: '📚 From Course Notes' },
      cached_answer: { badge: 'n8n-source-local', label: '💾 Cached Answer' },
      quiz_notes: { badge: 'n8n-source-local', label: '📝 Quiz Notes' },
      openai: { badge: 'n8n-source-ai', label: '🤖 AI Generated' },
      fallback: { badge: 'n8n-source-fallback', label: '💡 Suggestions' },
    };
    const s = sourceLabels[source] || sourceLabels.fallback;
    bubble.innerHTML = `
      <div class="n8n-chat-content">
        <div class="n8n-chat-answer">${formatMarkdown(text)}</div>
        <div class="n8n-chat-meta">
          <span class="n8n-source-badge ${s.badge}">${s.label}</span>
          ${responseTime ? `<span class="muted" style="font-size:0.75rem;">${responseTime}ms</span>` : ''}
        </div>
      </div>`;
  }
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

function askSuggestion(q) {
  document.getElementById('questionInput').value = q;
  document.getElementById('mentorForm').dispatchEvent(new Event('submit'));
}

// ── Study Planner ──────────────────────────────
function createStudyPlan() {
  const examName = document.getElementById('examName').value.trim();
  const examDate = document.getElementById('examDate').value;
  const courseIds = Array.from(document.querySelectorAll('.course-checkbox:checked')).map(c => parseInt(c.value));

  if (!examName || !examDate || courseIds.length === 0) {
    alert('Please fill in exam name, date, and select at least one course.');
    return;
  }

  fetch('/n8n/study-planner/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ exam_name: examName, exam_date: examDate, course_ids: courseIds }),
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) {
      alert(data.error);
    } else {
      alert(`Study plan created! ${data.total_tasks} tasks across ${data.total_days} days (~${data.minutes_per_day} min/day)`);
      location.reload();
    }
  });
}

function markDayComplete(planId) {
  // Find the day ID from the plan (simplified — complete today)
  fetch(`/n8n/study-planner/${planId}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      location.reload();
    }
  });
}

// ── Career ──────────────────────────────────────
function generateCareer() {
  const btn = document.getElementById('careerBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Generating...';

  fetch('/n8n/career/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) {
      alert(data.error);
      btn.disabled = false;
      btn.textContent = '🚀 Generate Recommendations';
    } else {
      location.reload();
    }
  })
  .catch(() => {
    btn.disabled = false;
    btn.textContent = '🚀 Generate Recommendations';
  });
}

// ── Feedback ──────────────────────────────────────
let currentRating = 0;

function setRating(rating) {
  currentRating = rating;
  document.querySelectorAll('.n8n-star').forEach((star, idx) => {
    star.textContent = idx < rating ? '★' : '☆';
    star.classList.toggle('active', idx < rating);
  });
}

function submitFeedback() {
  const text = document.getElementById('feedbackText').value.trim();
  const courseId = document.getElementById('feedbackCourse').value;

  if (!text) {
    alert('Please enter your feedback.');
    return;
  }

  const btn = document.getElementById('feedbackBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Submitting...';

  fetch('/n8n/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, course_id: courseId ? parseInt(courseId) : null, rating: currentRating || null }),
  })
  .then(r => r.json())
  .then(data => {
    const result = document.getElementById('feedbackResult');
    const emojis = { positive: '😊', neutral: '😐', negative: '😔' };
    result.innerHTML = `
      <div class="card" style="padding:16px;text-align:center;">
        <div style="font-size:2rem;">${emojis[data.sentiment] || '📝'}</div>
        <p>Thank you for your feedback!</p>
        <p class="muted">Sentiment: <strong>${data.sentiment}</strong> · Category: <strong>${data.category}</strong></p>
      </div>`;
    result.style.display = 'block';
    btn.textContent = '✅ Submitted';
    document.getElementById('feedbackText').value = '';
    setRating(0);
  })
  .catch(() => {
    btn.disabled = false;
    btn.textContent = 'Submit Feedback';
  });
}

// Sentiment preview on typing
if (document.getElementById('feedbackText')) {
  document.getElementById('feedbackText').addEventListener('input', function() {
    const text = this.value.toLowerCase();
    const preview = document.getElementById('sentimentPreview');
    const emoji = document.getElementById('sentimentEmoji');
    const label = document.getElementById('sentimentLabel');

    if (text.length < 10) { preview.style.display = 'none'; return; }

    const posWords = ['great','excellent','amazing','awesome','love','perfect','helpful','good','enjoy','useful'];
    const negWords = ['bad','terrible','awful','confusing','boring','poor','waste','frustrating','disappointed'];

    let pos = 0, neg = 0;
    posWords.forEach(w => { if (text.includes(w)) pos++; });
    negWords.forEach(w => { if (text.includes(w)) neg++; });

    preview.style.display = 'flex';
    if (pos > neg) { emoji.textContent = '😊'; label.textContent = 'Positive sentiment detected'; }
    else if (neg > pos) { emoji.textContent = '😔'; label.textContent = 'Negative sentiment detected'; }
    else { emoji.textContent = '😐'; label.textContent = 'Neutral sentiment'; }
  });
}

// ── Automation Builder ──────────────────────────
function addActionRow() {
  const container = document.getElementById('ruleActions');
  const row = container.querySelector('.n8n-action-row').cloneNode(true);
  row.querySelector('.n8n-action-params').value = '';
  container.appendChild(row);
}

function createRule() {
  const name = document.getElementById('ruleName').value.trim();
  const trigger = document.getElementById('ruleTrigger').value;

  if (!name) { alert('Rule name is required.'); return; }

  const actions = [];
  document.querySelectorAll('.n8n-action-row').forEach(row => {
    const action = row.querySelector('.n8n-action-select').value;
    const paramsRaw = row.querySelector('.n8n-action-params').value.trim();
    let params = {};
    if (paramsRaw) {
      try { params = JSON.parse(paramsRaw); } catch { params = { value: paramsRaw }; }
    }
    actions.push({ action, params });
  });

  fetch('/n8n/api/builder/rules', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, trigger_event: trigger, conditions: [], actions }),
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) { alert(data.error); }
    else { alert('Rule created!'); location.reload(); }
  });
}

function deleteRule(id) {
  if (!confirm('Delete this rule?')) return;
  fetch(`/n8n/api/builder/rules/${id}`, { method: 'DELETE' })
    .then(r => r.json())
    .then(data => { if (data.success) location.reload(); });
}

// ── Utility ──────────────────────────────────────
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatMarkdown(text) {
  // Simple markdown: bold, code, newlines
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}
