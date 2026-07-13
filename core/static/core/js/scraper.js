function resetRunButton() {
  const btn = document.getElementById("run-btn");
  btn.disabled  = false;
  btn.className = "run-btn";
  btn.textContent = "▶ Run Scraper";
}

let timerInterval = null;
let timerStart = null;

function formatElapsed(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  const pad = (n) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}

function startTimer() {
  const el = document.getElementById("run-timer");
  timerStart = Date.now();
  el.textContent = "Elapsed: 0:00";
  timerInterval = setInterval(() => {
    el.textContent = `Elapsed: ${formatElapsed(Date.now() - timerStart)}`;
  }, 1000);
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

function clearTimer() {
  stopTimer();
  document.getElementById("run-timer").textContent = "";
}

document.getElementById("scraper-form").addEventListener("htmx:beforeRequest", () => {
  document.getElementById("log-section").style.display = "block";
  document.getElementById("log-box").innerHTML = "";
  const btn = document.getElementById("run-btn");
  btn.disabled  = true;
  btn.className = "run-btn running";
  btn.textContent = "⟳ Running…";
  document.getElementById("stop-btn").style.display = "inline-block";
  startTimer();
});

document.body.addEventListener("htmx:afterSwap", (e) => {
  if (e.detail.target.closest && e.detail.target.closest("#status-region")) {
    const running = document.querySelector("#status-region .scraper-running");
    if (!running) {
      resetRunButton();
      document.getElementById("stop-btn").style.display = "none";
      stopTimer();
    }
  }
});

document.getElementById("stop-btn").addEventListener("htmx:responseError", (e) => {
  resetRunButton();
  clearTimer();
  document.getElementById("stop-btn").style.display = "none";
  document.getElementById("status-region").innerHTML = e.detail.xhr.responseText;
});

document.getElementById("scraper-form").addEventListener("htmx:responseError", (e) => {
  resetRunButton();
  clearTimer();
  document.getElementById("status-region").innerHTML = e.detail.xhr.responseText;
});

document.getElementById("hide-noise").addEventListener("change", (e) => {
  document.getElementById("log-box").classList.toggle("hide-noise", e.target.checked);
});

document.body.addEventListener("htmx:sseMessage", () => {
  const box = document.getElementById("log-box");
  while (box.children.length > 2000) {
    box.removeChild(box.firstChild);
  }
});

document.getElementById("scraper-form").addEventListener("submit", (e) => {
  const cleanBox = document.getElementById("clean");
  if (cleanBox.checked && !confirm("This clears all cached scrape progress (pass1, pass2, results) and starts completely fresh. Continue?")) {
    e.preventDefault();
  }
});

document.getElementById("clean").addEventListener("change", (e) => {
  const resumeBox = document.getElementById("resume");
  if (e.target.checked) {
    resumeBox.checked = false;
    resumeBox.disabled = true;
  } else {
    resumeBox.disabled = false;
  }
});


document.getElementById("resume").addEventListener("change", (e) => {
  const cleanBox = document.getElementById("clean");
  if (e.target.checked) {
    cleanBox.checked = false;
    cleanBox.disabled = true;
  } else {
    cleanBox.disabled = false;
  }
});

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

document.body.addEventListener("htmx:configRequest", (e) => {
  e.detail.headers["X-CSRFToken"] = getCookie("csrftoken");
});