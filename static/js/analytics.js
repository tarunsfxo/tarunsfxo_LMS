// tarunsfxo LMS - Analytics page charts powered by Chart.js

const palette = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

async function loadJSON(url) {
  const res = await fetch(url);
  return res.json();
}

async function renderCategoryChart() {
  const data = await loadJSON("/api/analytics/category-progress");
  new Chart(document.getElementById("categoryChart"), {
    type: "bar",
    data: {
      labels: data.labels,
      datasets: [
        { label: "Completed", data: data.completed, backgroundColor: "#6366f1" },
        { label: "Total", data: data.total, backgroundColor: "#e2e8f0" },
      ],
    },
    options: { responsive: true, scales: { y: { beginAtZero: true } } },
  });
}

async function renderWeeklyChart() {
  const data = await loadJSON("/api/analytics/weekly-activity");
  new Chart(document.getElementById("weeklyChart"), {
    type: "line",
    data: {
      labels: data.labels,
      datasets: [
        {
          label: "Bites Completed",
          data: data.counts,
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6,182,212,0.15)",
          fill: true,
          tension: 0.35,
        },
      ],
    },
    options: { responsive: true, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } },
  });
}

async function renderQuizChart() {
  const data = await loadJSON("/api/analytics/quiz-performance");
  new Chart(document.getElementById("quizChart"), {
    type: "line",
    data: {
      labels: data.labels,
      datasets: [
        {
          label: "Score %",
          data: data.scores,
          borderColor: "#10b981",
          backgroundColor: "rgba(16,185,129,0.15)",
          fill: true,
          tension: 0.35,
        },
      ],
    },
    options: { responsive: true, scales: { y: { beginAtZero: true, max: 100 } } },
  });
}

async function renderDifficultyChart() {
  const data = await loadJSON("/api/analytics/difficulty-breakdown");
  new Chart(document.getElementById("difficultyChart"), {
    type: "doughnut",
    data: {
      labels: data.labels,
      datasets: [{ data: data.counts, backgroundColor: palette }],
    },
    options: { responsive: true },
  });
}

document.addEventListener("DOMContentLoaded", () => {
  renderCategoryChart();
  renderWeeklyChart();
  renderQuizChart();
  renderDifficultyChart();
});
