// DevBites - bite detail page interactions

document.addEventListener("DOMContentLoaded", () => {
  const completeBtn = document.getElementById("completeBtn");
  const uncompleteBtn = document.getElementById("uncompleteBtn");

  if (completeBtn) {
    completeBtn.addEventListener("click", async () => {
      const biteId = completeBtn.dataset.biteId;
      completeBtn.disabled = true;
      completeBtn.textContent = "Saving...";
      try {
        const result = await postForm(`/bites/${biteId}/complete`);
        if (result.success) {
          completeBtn.textContent = "Completed";
          completeBtn.classList.remove("btn-success");
          completeBtn.classList.add("btn-outline");
          if (uncompleteBtn) uncompleteBtn.style.display = "";
          if (result.certificate_issued) {
            showCertificateModal(result.cert_category);
          } else {
            showToast(`+10 XP earned! Now Level ${result.level}, ${result.streak} day streak 🔥`);
          }
        }
      } catch (e) {
        completeBtn.disabled = false;
        completeBtn.textContent = "Mark Complete";
      }
    });
  }

  if (uncompleteBtn) {
    uncompleteBtn.addEventListener("click", async () => {
      const biteId = uncompleteBtn.dataset.biteId;
      uncompleteBtn.disabled = true;
      try {
        const result = await postForm(`/bites/${biteId}/uncomplete`);
        if (result.success) {
          uncompleteBtn.style.display = "none";
          uncompleteBtn.disabled = false;
          if (completeBtn) {
            completeBtn.disabled = false;
            completeBtn.textContent = "Mark Complete";
            completeBtn.classList.remove("btn-outline");
            completeBtn.classList.add("btn-success");
          }
          showToast("Marked as incomplete. You can redo this lesson anytime.");
        }
      } catch (e) {
        uncompleteBtn.disabled = false;
      }
    });
  }

  document.querySelectorAll(".quiz-question").forEach((qEl) => {
    qEl.querySelectorAll(".quiz-option").forEach((opt) => {
      opt.addEventListener("click", () => {
        qEl.querySelectorAll(".quiz-option").forEach((o) => o.classList.remove("selected"));
        opt.classList.add("selected");
        qEl.dataset.selected = opt.dataset.option;
      });
    });
  });

  const quizForm = document.getElementById("quizForm");
  if (quizForm) {
    quizForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const answers = {};
      document.querySelectorAll(".quiz-question").forEach((qEl) => {
        const qid = qEl.dataset.questionId;
        if (qEl.dataset.selected) answers[qid] = qEl.dataset.selected;
      });

      const result = await postJSON(`/bites/${window.BITE_ID}/quiz`, { answers });
      const resultEl = document.getElementById("quizResult");

      if (result.success) {
        const xpNote = result.xp_awarded
          ? ""
          : " (XP already earned on a previous attempt)";
        resultEl.innerHTML = `You scored <strong>${result.score}/${result.total}</strong>. Total XP: ${result.xp}${xpNote}`;
        result.results.forEach((r) => {
          const qEl = document.querySelector(`.quiz-question[data-question-id="${r.question_id}"]`);
          if (!qEl) return;
          qEl.querySelectorAll(".quiz-option").forEach((opt) => {
            if (opt.dataset.option === r.correct_option) opt.classList.add("correct");
            else if (opt.classList.contains("selected") && !r.correct) opt.classList.add("incorrect");
          });
          const expEl = qEl.querySelector(".explanation");
          if (expEl && r.explanation) {
            expEl.textContent = "💡 " + r.explanation;
            expEl.style.display = "block";
          }
        });
        quizForm.querySelector("button[type=submit]").disabled = true;
      }
    });
  }
});

function showToast(message) {
  const toast = document.createElement("div");
  toast.textContent = message;
  toast.style.position = "fixed";
  toast.style.bottom = "24px";
  toast.style.right = "24px";
  toast.style.background = "#0f172a";
  toast.style.color = "#fff";
  toast.style.padding = "14px 20px";
  toast.style.borderRadius = "10px";
  toast.style.boxShadow = "0 8px 24px rgba(0,0,0,0.2)";
  toast.style.zIndex = "1000";
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = "opacity 0.4s";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

function showCertificateModal(categoryName) {
  // Overlay
  const overlay = document.createElement("div");
  overlay.style.cssText = `
    position:fixed;inset:0;background:rgba(0,0,0,0.65);
    display:flex;align-items:center;justify-content:center;
    z-index:2000;animation:fadeIn 0.3s ease;
  `;

  // Modal card
  const modal = document.createElement("div");
  modal.style.cssText = `
    background:linear-gradient(160deg,#FDFAF4 0%,#F5EDD6 100%);
    border:2px solid #C9A84C;
    border-radius:16px;
    padding:48px 56px;
    max-width:480px;
    width:90%;
    text-align:center;
    box-shadow:0 24px 64px rgba(0,0,0,0.35),inset 0 0 0 6px rgba(201,168,76,0.12);
    animation:popIn 0.4s cubic-bezier(0.34,1.56,0.64,1);
    position:relative;
    overflow:hidden;
  `;

  // Corner ornaments (CSS pseudo via inline elements)
  ["top:12px;left:12px", "top:12px;right:12px", "bottom:12px;left:12px", "bottom:12px;right:12px"].forEach(pos => {
    const orn = document.createElement("div");
    orn.textContent = "✦";
    orn.style.cssText = `position:absolute;${pos};color:#C9A84C;font-size:14px;opacity:0.6;`;
    modal.appendChild(orn);
  });

  modal.innerHTML += `
    <div style="font-size:52px;margin-bottom:8px;">🏆</div>
    <div style="color:#8B6914;font-size:11px;letter-spacing:3px;text-transform:uppercase;font-weight:700;margin-bottom:6px;">
      Certificate Earned
    </div>
    <h2 style="color:#1A1200;font-size:24px;margin:8px 0;font-weight:800;">
      Congratulations! 🎉
    </h2>
    <p style="color:#5C4A1E;font-size:14px;line-height:1.6;margin:12px 0 24px;">
      You've completed the entire <strong>${categoryName}</strong> learning track.<br>
      Your certificate has been generated and is ready to download!
    </p>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
      <a href="/certificates" style="
        background:linear-gradient(135deg,#C9A84C,#E8D08A);
        color:#1A1200;font-weight:700;
        padding:12px 28px;border-radius:8px;
        text-decoration:none;font-size:14px;
        box-shadow:0 4px 14px rgba(201,168,76,0.4);
        transition:transform 0.2s;
      " onmouseover="this.style.transform='translateY(-2px)'"
         onmouseout="this.style.transform=''">
        📄 View & Download Certificate
      </a>
      <button onclick="this.closest('.cert-overlay').remove()" style="
        background:transparent;border:1.5px solid #C9A84C;
        color:#8B6914;font-weight:600;
        padding:12px 20px;border-radius:8px;
        cursor:pointer;font-size:14px;
      ">
        Continue Learning
      </button>
    </div>
  `;

  overlay.classList.add("cert-overlay");
  overlay.appendChild(modal);
  overlay.addEventListener("click", e => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);

  // Inject keyframe animations once
  if (!document.getElementById("certAnimStyles")) {
    const style = document.createElement("style");
    style.id = "certAnimStyles";
    style.textContent = `
      @keyframes fadeIn { from{opacity:0} to{opacity:1} }
      @keyframes popIn  { from{opacity:0;transform:scale(0.7)} to{opacity:1;transform:scale(1)} }
    `;
    document.head.appendChild(style);
  }
}
