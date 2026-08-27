/* ==========================================================
   CareerCoach AI - Career Tracker dashboard
   Handles: role selection, skill-gap rendering, roadmap tabs,
   quiz modal, and the progress trend chart.
   Kept in its own file — does not touch static/js/main.js.
   ========================================================== */

(function () {
  const root = document.getElementById("careerDashboard");
  if (!root) return; // not on this page

  const initial = window.__CAREER_DASHBOARD_INITIAL__ || {};
  let state = {
    roleKey: initial.confirmedRoleKey || null,
    gapAnalysis: initial.gapAnalysis || null,
    roadmap: initial.roadmap || null,
    progressMap: initial.progressMap || {},
    availableQuizSkills: initial.availableQuizSkills || [],
    skillNameToKey: initial.skillNameToKey || {},
    activeStage: "beginner",
  };

  const dashboardBody = document.getElementById("careerDashboardBody");
  const readinessRoleName = document.getElementById("readinessRoleName");
  const readinessRing = document.getElementById("readinessRing");
  const readinessPctLabel = document.getElementById("readinessPctLabel");
  const gapStrengthsList = document.getElementById("gapStrengthsList");
  const gapImproveList = document.getElementById("gapImproveList");
  const gapMissingList = document.getElementById("gapMissingList");
  const gapNotAssessedList = document.getElementById("gapNotAssessedList");
  const roadmapStageContent = document.getElementById("roadmapStageContent");
  const roadmapTabs = document.querySelectorAll(".roadmap-tab");
  const reassessBtn = document.getElementById("reassessBtn");
  const roleSubmitBtn = document.getElementById("roleSubmitBtn");

  // Sections revealed one-by-one, in order, once the role is confirmed.
  const revealSectionEls = ["readinessCard", "skillComparisonCard", "roadmapCard", "progressCard"]
    .map((id) => document.getElementById(id))
    .filter(Boolean);

  // Track which role is highlighted but not yet confirmed via the
  // "Confirm & Start Tracking" button. Seeded either from a role the
  // user already confirmed in a past visit, or from a "?role=" deep
  // link coming from the Career Recommendation page.
  let pendingRoleKey = initial.preselectRoleKey || null;

  // ---------- Role picking (selection only — does not load data) --
  document.querySelectorAll(".role-pick-card").forEach((card) => {
    card.addEventListener("click", () => pickRole(card.getAttribute("data-role-key"), card));
  });

  function pickRole(roleKey, cardEl) {
    document.querySelectorAll(".role-pick-card").forEach((c) => c.classList.remove("is-selected"));
    if (cardEl) cardEl.classList.add("is-selected");

    pendingRoleKey = roleKey;
    if (roleSubmitBtn) roleSubmitBtn.disabled = false;
  }

  // ---------- Submit / Continue — confirms the role, then loads &
  // reveals the rest of the dashboard sequentially -------------------
  if (roleSubmitBtn) {
    roleSubmitBtn.addEventListener("click", () => {
      if (!pendingRoleKey) return;
      confirmRole(pendingRoleKey);
    });
  }

  function confirmRole(roleKey) {
    roleSubmitBtn.disabled = true;
    const originalBtnHtml = roleSubmitBtn.innerHTML;
    roleSubmitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Analyzing...';

    roadmapStageContent.innerHTML =
      '<div class="loading-box"><div class="spinner-border"></div><p>Analyzing your skills...</p></div>';

    fetch("/api/career/select-role", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role_key: roleKey }),
    })
      .then((r) => r.json())
      .then((data) => {
        roleSubmitBtn.disabled = false;
        roleSubmitBtn.innerHTML = originalBtnHtml;

        if (data.error) {
          roadmapStageContent.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
          return;
        }
        state.roleKey = roleKey;
        state.gapAnalysis = data.gap_analysis;
        state.roadmap = data.roadmap;
        state.progressMap = {}; // freshly selected role - progress recalculated server-side on load

        renderAll();
        revealDashboard();
        loadProgressChart();
      })
      .catch(() => {
        roleSubmitBtn.disabled = false;
        roleSubmitBtn.innerHTML = originalBtnHtml;
        roadmapStageContent.innerHTML =
          '<div class="alert alert-danger">Could not load this role right now. Please try again.</div>';
      });
  }

  // Reveals the dashboard sections one at a time with a short stagger,
  // so the page reads as a guided assessment instead of a data dump.
  function revealDashboard() {
    dashboardBody.classList.remove("d-none");
    revealSectionEls.forEach((el, i) => {
      el.classList.remove("is-visible");
      // Force reflow so the transition replays even if this role was
      // confirmed once already.
      void el.offsetWidth;
      setTimeout(() => el.classList.add("is-visible"), i * 220 + 120);
    });
    dashboardBody.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // ---------- Rendering ----------------------------------------
  function renderAll() {
    if (!state.gapAnalysis) return;

    readinessRoleName.textContent = state.gapAnalysis.role.name;
    animateRing(readinessRing, state.gapAnalysis.readiness_pct);
    readinessPctLabel.textContent = state.gapAnalysis.readiness_pct + "%";

    // Skill Comparison is driven live by assessment scores (80-100%
    // Strength, 60-79% Needs Improvement, 0-59% Skill Gap, no attempt
    // yet -> Not Yet Assessed) — see gap_analysis.skill_status.
    const status = state.gapAnalysis.skill_status || {};
    renderSkillList(gapStrengthsList, status.strength, "strength");
    renderSkillList(gapImproveList, status.needs_improvement, "improve");
    renderSkillList(gapMissingList, status.skill_gap, "gap");
    renderSkillList(gapNotAssessedList, status.not_assessed, "not-assessed");

    renderRoadmapStage(state.activeStage);
  }

  function animateRing(circle, pct) {
    if (!circle) return;
    const offset = 264 - (264 * pct) / 100;
    circle.style.transition = "none";
    circle.style.strokeDashoffset = 264;
    circle.getBoundingClientRect();
    circle.style.transition = "";
    requestAnimationFrame(() => {
      circle.style.strokeDashoffset = offset;
    });
  }

  function renderSkillList(container, items, kind) {
    if (!container) return;
    if (!items || !items.length) {
      container.innerHTML = '<p class="empty-message mb-0">Nothing here yet.</p>';
      return;
    }

    container.innerHTML = "";
    items.forEach((item) => {
      const chip = document.createElement("div");
      chip.className = "gap-skill-chip gap-skill-" + kind;

      const label = document.createElement("span");
      label.textContent = item.name;
      chip.appendChild(label);

      if (typeof item.percentage === "number") {
        const pctSpan = document.createElement("span");
        pctSpan.className = "gap-skill-pct";
        pctSpan.textContent = Math.round(item.percentage) + "%";
        chip.appendChild(pctSpan);
      } else {
        const noteSpan = document.createElement("span");
        noteSpan.className = "gap-skill-pct gap-skill-note";
        noteSpan.textContent = "Not yet assessed";
        chip.appendChild(noteSpan);
      }

      const skillKey = state.skillNameToKey[item.name];
      if (skillKey && state.availableQuizSkills.includes(skillKey)) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "gap-skill-quiz-btn";
        btn.innerHTML = '<i class="bi bi-pencil-square"></i>';
        btn.title = "Take assessment";
        btn.addEventListener("click", () => openQuiz(skillKey, item.name));
        chip.appendChild(btn);
      }

      container.appendChild(chip);
    });
  }

  // ---------- Roadmap tabs --------------------------------------
  roadmapTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      roadmapTabs.forEach((t) => t.classList.remove("is-active"));
      tab.classList.add("is-active");
      state.activeStage = tab.getAttribute("data-stage");
      renderRoadmapStage(state.activeStage);
    });
  });

  function renderRoadmapStage(stage) {
    if (!roadmapStageContent) return;
    if (!state.roadmap) {
      roadmapStageContent.innerHTML =
        '<p class="empty-message mb-0">Select a role above to generate your roadmap.</p>';
      return;
    }

    const items = state.roadmap[stage] || [];
    if (!items.length) {
      roadmapStageContent.innerHTML =
        '<p class="empty-message mb-0">Nothing scheduled for this stage right now.</p>';
      return;
    }

    roadmapStageContent.innerHTML = "";
    items.forEach((item) => {
      const skillKey = state.skillNameToKey[item.skill] || "";
      const status = state.progressMap[skillKey] || "pending";

      const card = document.createElement("div");
      card.className = "roadmap-item";

      card.innerHTML = `
        <div class="roadmap-item-top">
          <div class="roadmap-item-skill">${escapeHtml(item.skill || "")}</div>
          <span class="roadmap-status roadmap-status-${status}">${statusLabel(status)}</span>
        </div>
        <p class="roadmap-item-focus">${escapeHtml(item.focus || "")}</p>
        <p class="roadmap-item-practice"><i class="bi bi-tools me-1"></i>${escapeHtml(item.practice || "")}</p>
        ${renderRoadmapResources(item.resources)}
      `;

      const actions = document.createElement("div");
      actions.className = "roadmap-item-actions";

      if (state.availableQuizSkills.includes(skillKey)) {
        const quizBtn = document.createElement("button");
        quizBtn.type = "button";
        quizBtn.className = "btn btn-primary btn-sm";
        quizBtn.innerHTML = '<i class="bi bi-pencil-square me-1"></i> Take Assessment';
        quizBtn.addEventListener("click", () => openQuiz(skillKey, item.skill, stage));
        actions.appendChild(quizBtn);
      }

      if (status !== "completed") {
        const markBtn = document.createElement("button");
        markBtn.type = "button";
        markBtn.className = "btn btn-outline-primary btn-sm";
        markBtn.innerHTML = '<i class="bi bi-check2 me-1"></i> Mark In Progress';
        markBtn.addEventListener("click", () =>
          updateRoadmapStatus(stage, skillKey, "in_progress", markBtn, card)
        );
        actions.appendChild(markBtn);
      }

      card.appendChild(actions);
      roadmapStageContent.appendChild(card);
    });
  }

  // Curated resources come from the backend (career_data.SKILL_RESOURCES)
  // — never invented client-side. Renders nothing if none are available
  // for a skill rather than padding with a placeholder link.
  function renderRoadmapResources(resources) {
    if (!resources || !resources.length) return "";
    const links = resources
      .map(
        (r) =>
          `<a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer" class="roadmap-resource-link">
            <i class="bi bi-box-arrow-up-right me-1"></i>${escapeHtml(r.name)}
          </a>`
      )
      .join("");
    return `<div class="roadmap-item-resources"><span class="roadmap-resources-label">Learning resources</span>${links}</div>`;
  }

  function statusLabel(status) {
    return { pending: "Pending", in_progress: "In Progress", completed: "Completed" }[status] || "Pending";
  }

  function updateRoadmapStatus(stage, skillKey, status, btn, card) {
    if (!skillKey) return;
    fetch("/api/career/roadmap/status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role_key: state.roleKey, stage: stage, skill_key: skillKey, status: status }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.ok) {
          state.progressMap[skillKey] = status;
          renderRoadmapStage(state.activeStage);
        }
      });
  }

  // ---------- Reassess / regenerate roadmap ----------------------
  if (reassessBtn) {
    reassessBtn.addEventListener("click", () => {
      if (!state.roleKey) return;
      reassessBtn.disabled = true;
      reassessBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i> Regenerating...';

      fetch("/api/career/roadmap/regenerate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role_key: state.roleKey }),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.gap_analysis) state.gapAnalysis = data.gap_analysis;
          if (data.roadmap) state.roadmap = data.roadmap;
          renderAll();
        })
        .finally(() => {
          reassessBtn.disabled = false;
          reassessBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i> Reassess &amp; Regenerate';
        });
    });
  }

  // ---------- Quiz modal -------------------------------------------
  const quizBackdrop = document.getElementById("quizModalBackdrop");
  const quizTitle = document.getElementById("quizModalTitle");
  const quizBody = document.getElementById("quizModalBody");
  const quizClose = document.getElementById("quizModalClose");

  function openQuiz(skillKey, skillLabel) {
    quizTitle.textContent = (skillLabel || skillKey) + " Assessment";
    quizBody.innerHTML =
      '<div class="loading-box"><div class="spinner-border"></div><p>Loading questions...</p></div>';
    quizBackdrop.classList.add("is-open");

    fetch("/api/career/quiz/" + encodeURIComponent(skillKey))
      .then((r) => r.json())
      .then((data) => {
        if (data.error) {
          quizBody.innerHTML = `<div class="alert alert-warning mb-0">${data.error}</div>`;
          return;
        }
        renderQuizForm(skillKey, data.questions);
      })
      .catch(() => {
        quizBody.innerHTML = '<div class="alert alert-danger mb-0">Could not load the assessment.</div>';
      });
  }

  function renderQuizForm(skillKey, questions) {
    const optionLetters = ["A", "B", "C", "D", "E", "F"];
    let html = '<form id="quizForm">';
    questions.forEach((q) => {
      html += `<div class="quiz-question">
        <p class="quiz-question-text">${q.index + 1}. ${escapeHtml(q.question)}</p>
        <div class="quiz-options">`;
      q.options.forEach((opt, i) => {
        html += `
          <label class="quiz-option">
            <input type="radio" name="q${q.index}" value="${i}" required />
            <span>${optionLetters[i] || i}. ${escapeHtml(opt)}</span>
          </label>`;
      });
      html += `</div></div>`;
    });
    html += '<button type="submit" class="btn btn-primary w-100 mt-2">Submit Assessment</button></form>';
    quizBody.innerHTML = html;

    document.getElementById("quizForm").addEventListener("submit", function (e) {
      e.preventDefault();
      const answers = {};
      questions.forEach((q) => {
        const checked = this.querySelector(`input[name="q${q.index}"]:checked`);
        answers[q.index] = checked ? parseInt(checked.value, 10) : -1;
      });
      submitQuiz(skillKey, answers);
    });
  }

  function submitQuiz(skillKey, answers) {
    quizBody.innerHTML =
      '<div class="loading-box"><div class="spinner-border"></div><p>Scoring your answers...</p></div>';

    fetch("/api/career/quiz/" + encodeURIComponent(skillKey) + "/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role_key: state.roleKey, answers: answers }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.error) {
          quizBody.innerHTML = `<div class="alert alert-danger mb-0">${data.error}</div>`;
          return;
        }
        renderQuizResult(data);
        // Refresh gap analysis + roadmap status in the background
        if (state.roleKey) refreshAfterQuiz();
      })
      .catch(() => {
        quizBody.innerHTML = '<div class="alert alert-danger mb-0">Could not submit the assessment.</div>';
      });
  }

  function renderQuizResult(data) {
    let html = `
      <div class="quiz-result">
        <div class="quiz-result-score">${data.score}/${data.total}</div>
        <div class="quiz-result-pct">${data.percentage}% correct</div>
      </div>
      <div class="quiz-feedback-list">`;

    data.feedback.forEach((f, i) => {
      html += `
        <div class="quiz-feedback-item ${f.is_correct ? "is-correct" : "is-incorrect"}">
          <div class="quiz-feedback-q">${i + 1}. ${escapeHtml(f.question)}</div>
          <div class="quiz-feedback-a">
            <i class="bi ${f.is_correct ? "bi-check-circle-fill" : "bi-x-circle-fill"}"></i>
            Correct answer: ${escapeHtml(f.correct_option)}
          </div>
        </div>`;
    });

    html += `</div><button type="button" class="btn btn-outline-primary w-100 mt-3" id="quizDoneBtn">Close</button>`;
    quizBody.innerHTML = html;
    document.getElementById("quizDoneBtn").addEventListener("click", closeQuiz);
  }

  function refreshAfterQuiz() {
    // Lightweight refresh: re-reads gap analysis + roadmap progress
    // from the DB only. Never touches the roadmap cache and never
    // calls Gemini, so every assessment can safely trigger it.
    fetch("/api/career/refresh")
      .then((r) => r.json())
      .then((data) => {
        if (data.gap_analysis) state.gapAnalysis = data.gap_analysis;
        if (data.progress_map) state.progressMap = data.progress_map;
        renderAll();
        loadProgressChart();
      });
  }

  function closeQuiz() {
    quizBackdrop.classList.remove("is-open");
  }
  if (quizClose) quizClose.addEventListener("click", closeQuiz);
  if (quizBackdrop) {
    quizBackdrop.addEventListener("click", (e) => {
      if (e.target === quizBackdrop) closeQuiz();
    });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }

  // ---------- Progress chart --------------------------------------
  let progressChartInstance = null;

  function loadProgressChart() {
    fetch("/api/career/progress")
      .then((r) => r.json())
      .then((data) => {
        renderAssessmentHistory(data.trend || []);

        const canvas = document.getElementById("progressChart");
        const emptyMsg = document.getElementById("progressChartEmpty");
        if (!data.trend || !data.trend.length) {
          if (canvas) canvas.style.display = "none";
          if (emptyMsg) emptyMsg.style.display = "block";
          return;
        }
        if (emptyMsg) emptyMsg.style.display = "none";
        if (canvas) canvas.style.display = "block";

        const labels = data.trend.map((t, i) => "Attempt " + (i + 1) + " (" + t.skill_name + ")");
        const values = data.trend.map((t) => t.percentage);

        if (progressChartInstance) progressChartInstance.destroy();
        if (window.Chart && canvas) {
          progressChartInstance = new Chart(canvas, {
            type: "line",
            data: {
              labels: labels,
              datasets: [
                {
                  label: "Assessment score (%)",
                  data: values,
                  borderColor: "#4f46e5",
                  backgroundColor: "rgba(79,70,229,.12)",
                  tension: 0.35,
                  fill: true,
                },
              ],
            },
            options: {
              scales: { y: { min: 0, max: 100 } },
              plugins: { legend: { display: false } },
            },
          });
        }
      })
      .catch(() => {});
  }

  // Full Assessment History list (every attempt kept, newest first) —
  // the trend chart above only plots the numbers; this shows exactly
  // which skill/date/score each attempt was, per-skill classification
  // included for a quick read.
  function renderAssessmentHistory(trend) {
    const list = document.getElementById("assessmentHistoryList");
    if (!list) return;
    if (!trend.length) {
      list.innerHTML = "";
      return;
    }

    const rows = trend.slice().reverse(); // newest first
    list.innerHTML = rows
      .map((t) => {
        const pct = Math.round(t.percentage);
        const cls = pct >= 80 ? "is-strength" : pct >= 60 ? "is-needs-improvement" : "is-skill-gap";
        const date = new Date(t.taken_at);
        const dateLabel = isNaN(date.getTime()) ? "" : date.toLocaleDateString();
        return `
          <div class="assessment-history-item">
            <span>
              <span class="assessment-history-skill">${escapeHtml(t.skill_name)}</span>
              <span class="assessment-history-date">${dateLabel}</span>
            </span>
            <span class="assessment-history-pct ${cls}">${pct}%</span>
          </div>`;
      })
      .join("");
  }

  // ---------- Init ---------------------------------------------------
  // Sections stay hidden until the user clicks Continue/Submit — see
  // pickRole()/confirmRole() above. If a role was already selected in
  // a previous visit, its data is still available in `state` (cached
  // from the server) and its card is pre-highlighted so Continue works
  // immediately, but nothing is revealed until that click happens.
})();
