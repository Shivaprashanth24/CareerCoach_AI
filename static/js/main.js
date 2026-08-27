/* ==========================================================
   CareerCoach AI - main JavaScript
   Handles: skills chart, career recommendation, chatbot,
   plus UI-only enhancements (nav shadow, toasts, reveal
   animations, dropzone preview, expand/collapse).
   ========================================================== */

// ---------- 1. Skills chart (Chart.js) --------------------
function drawSkillsChart(skills) {
  const canvas = document.getElementById("skillsChart");
  if (!canvas || !skills.length) return;

  new Chart(canvas, {
    type: "bar",
    data: {
      labels: skills,
      // Simple demo strength value for every detected skill
      datasets: [{ label: "Skill detected", data: skills.map(() => 1), backgroundColor: "#4f46e5" }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { y: { display: false } },
    },
  });
}

// ---------- 2. Career recommendation (Gemini) -------------
function loadRecommendation() {
  const box = document.getElementById("recommendationBox");
  if (!box) return;

  box.textContent = "Generating your career guidance...";

  fetch("/api/recommendation")
    .then((response) => response.json())
    .then((data) => {
      box.innerHTML = marked.parse(data.reply);
    })
    .catch(() => {
      box.textContent = "Something went wrong. Please try again.";
    });
}

// ---------- 3. Chatbot ------------------------------------
function addBubble(text, who) {
  const window_ = document.getElementById("chatWindow");
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble " + (who === "user" ? "chat-user" : "chat-bot");
  bubble.innerHTML = text;
  window_.appendChild(bubble);
  window_.scrollTop = window_.scrollHeight;
  return bubble;
}

function addTypingBubble() {
  const bubble = addBubble(
    '<span class="typing-dots"><span></span><span></span><span></span></span>',
    "bot"
  );
  return bubble;
}

function setupChat() {
  const form = document.getElementById("chatForm");
  if (!form) return;

  const quickQuestions = document.querySelector(".quick-questions");

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    const input = document.getElementById("chatInput");
    const question = input.value.trim();
    if (!question) return;

    // Once the conversation is underway, the chatbot drives the next
    // question itself — the predefined starter buttons are no longer
    // relevant and would suggest a topic switch instead of an answer.
    if (quickQuestions) quickQuestions.classList.add("d-none");

    addBubble(escapeHtml(question), "user");
    input.value = "";
    const loading = addTypingBubble();

    const interestsField = document.getElementById("interestsInput");
    const interests = interestsField ? interestsField.value.trim() : "";

    fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question: question, interests: interests }),
    })
      .then((response) => response.json())
      .then((data) => {
        loading.innerHTML = data.reply;
      })
      .catch(() => {
        loading.textContent = "Sorry, I could not answer right now.";
      });
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------- 4. Navbar scroll shadow ------------------------
function setupNavbarScroll() {
  const nav = document.getElementById("siteNavbar");
  if (!nav) return;
  const toggle = () => {
    nav.classList.toggle("is-scrolled", window.scrollY > 8);
  };
  toggle();
  window.addEventListener("scroll", toggle, { passive: true });
}

// ---------- 5. Auto-dismiss flash toasts --------------------
function setupFlashToasts() {
  const stack = document.getElementById("flashStack");
  if (!stack) return;
  const alerts = stack.querySelectorAll(".alert");
  alerts.forEach((alert, i) => {
    setTimeout(() => {
      alert.style.transition = "opacity .4s ease, transform .4s ease";
      alert.style.opacity = "0";
      alert.style.transform = "translateX(20px)";
      setTimeout(() => alert.remove(), 400);
    }, 4500 + i * 300);
  });
}

// ---------- 6. Reveal-on-scroll entrance animations ---------
function setupRevealAnimations() {
  const targets = document.querySelectorAll(
    ".feature-card, .dashboard-card, .analysis-card, .recommendation-card, .overview-stat"
  );
  if (!targets.length) return;

  targets.forEach((el) => el.classList.add("reveal"));

  if (!("IntersectionObserver" in window)) {
    targets.forEach((el) => el.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.08 }
  );

  targets.forEach((el, i) => {
    el.style.transitionDelay = Math.min(i * 40, 240) + "ms";
    observer.observe(el);
  });
}

// ---------- 7. Upload dropzone preview -----------------------
function setupDropzone() {
  const zone = document.querySelector(".dropzone");
  if (!zone) return;
  const input = zone.querySelector('input[type="file"]');
  const label = zone.querySelector(".dz-filename");
  const labelText = label ? label.querySelector("span") : null;
  if (!input) return;

  const showName = (name) => {
    if (!label) return;
    if (labelText) labelText.textContent = name;
    else label.textContent = name;
    label.classList.add("is-active");
  };

  input.addEventListener("change", () => {
    if (input.files && input.files[0]) showName(input.files[0].name);
  });

  ["dragenter", "dragover"].forEach((evt) =>
    zone.addEventListener(evt, (e) => {
      e.preventDefault();
      zone.classList.add("is-dragover");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    zone.addEventListener(evt, (e) => {
      e.preventDefault();
      zone.classList.remove("is-dragover");
    })
  );
  zone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      input.files = e.dataTransfer.files;
      showName(e.dataTransfer.files[0].name);
    }
  });
}

// ---------- 8. Merge wrapped bullet fragments -----------------
// The resume parser stores each extracted PDF line as its own list
// item, so a single bullet point that wraps across several lines in
// the source resume shows up as several <li> fragments. This merges
// consecutive fragments back into one bullet. Purely a display fix —
// the underlying resume data is never changed.
function isCompleteBulletLine(buffer) {
  // Ends with sentence-final punctuation (optionally inside a quote
  // or bracket) — the bullet is finished.
  if (/[.!?;:]["')\]]?$/.test(buffer)) return true;

  // Looks like a standalone "Company Name  MONTH(YEAR)-MONTH(YEAR)"
  // or date-range line — these are already complete on their own,
  // even without trailing punctuation.
  if (/\(?\d{4}\)?\s*[-\u2013\u2014]\s*\(?\d{4}\)?/.test(buffer)) return true;
  if (
    /\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s*\(?\d{4}\)?/i.test(
      buffer
    )
  )
    return true;

  return false;
}

function mergeWrappedBullets() {
  document.querySelectorAll(".resume-entry ul").forEach((ul) => {
    const items = Array.from(ul.querySelectorAll(":scope > li"))
      .map((li) => li.textContent.trim())
      .filter(Boolean);

    if (items.length <= 1) return;

    const merged = [];
    let buffer = "";

    items.forEach((text) => {
      buffer = buffer ? buffer + " " + text : text;
      if (isCompleteBulletLine(buffer)) {
        merged.push(buffer.trim());
        buffer = "";
      }
    });
    if (buffer.trim()) merged.push(buffer.trim());

    // Nothing to merge — leave the list exactly as rendered.
    if (merged.length === items.length) return;

    ul.innerHTML = "";
    merged.forEach((text) => {
      const li = document.createElement("li");
      li.textContent = text;
      ul.appendChild(li);
    });
  });
}

// ---------- 9. Hero headline carousel (index page) ------------
function setupHeroCarousel() {
  const slides = document.querySelectorAll("#heroSlides .hero-slide");
  const dots = document.querySelectorAll("#heroDots .dot-track");
  const prevBtn = document.getElementById("heroPrev");
  const nextBtn = document.getElementById("heroNext");
  if (!slides.length) return;

  let index = 0;
  let timer = null;

  function show(i) {
    index = (i + slides.length) % slides.length;
    slides.forEach((s, n) => s.classList.toggle("is-active", n === index));
    dots.forEach((d, n) => d.classList.toggle("is-active", n === index));
  }

  function restart() {
    if (timer) clearInterval(timer);
    timer = setInterval(() => show(index + 1), 6000);
  }

  dots.forEach((dot, n) => {
    dot.addEventListener("click", () => {
      show(n);
      restart();
    });
  });
  if (prevBtn) prevBtn.addEventListener("click", () => { show(index - 1); restart(); });
  if (nextBtn) nextBtn.addEventListener("click", () => { show(index + 1); restart(); });

  show(0);
  restart();
}

// ---------- 10. Animated progress rings ------------------------
function setupProgressRings() {
  const rings = document.querySelectorAll(".js-ring");
  if (!rings.length) return;

  const animate = (circle) => {
    const target = circle.getAttribute("data-offset");
    if (target === null) return;
    // Force a reflow so the browser registers the starting value
    // before transitioning to the target offset.
    // eslint-disable-next-line no-unused-expressions
    circle.getBoundingClientRect();
    requestAnimationFrame(() => {
      circle.style.strokeDashoffset = target;
    });
  };

  if (!("IntersectionObserver" in window)) {
    rings.forEach(animate);
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animate(entry.target);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.2 }
  );
  rings.forEach((ring) => observer.observe(ring));
}

// ---------- 11. Expand / collapse long resume entry lists -----
function setupExpandCollapse() {
  document.querySelectorAll(".entry-group[data-max]").forEach((group) => {
    const max = parseInt(group.getAttribute("data-max"), 10) || 3;
    const entries = Array.from(group.querySelectorAll(".resume-entry"));
    if (entries.length <= max) return;

    group.classList.add("is-collapsible");
    entries.slice(max).forEach((el) => el.classList.add("is-hidden"));

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "show-more-btn";
    btn.innerHTML = `<span>Show ${entries.length - max} more</span> <i class="bi bi-chevron-down"></i>`;
    group.appendChild(btn);

    btn.addEventListener("click", () => {
      const isOpen = btn.classList.toggle("is-open");
      entries.slice(max).forEach((el) => el.classList.toggle("is-hidden", !isOpen));
      btn.querySelector("span").textContent = isOpen
        ? "Show less"
        : `Show ${entries.length - max} more`;
    });
  });
}

// ---------- Run on page load ------------------------------
document.addEventListener("DOMContentLoaded", function () {
  setupChat();
  setupNavbarScroll();
  setupFlashToasts();
  setupRevealAnimations();
  setupDropzone();
  mergeWrappedBullets();
  setupHeroCarousel();
  setupProgressRings();
  setupExpandCollapse();
});
