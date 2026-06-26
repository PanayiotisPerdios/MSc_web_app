document.getElementById("scraper-form").addEventListener("htmx:beforeRequest", () => {
  document.getElementById("log-section").style.display = "block";
  document.getElementById("log-box").innerHTML = "";
  const btn = document.getElementById("run-btn");
  btn.disabled  = true;
  btn.className = "run-btn running";
  btn.textContent = "⟳ Running…";
});

document.body.addEventListener("htmx:afterSwap", (e) => {
  if (e.detail.target.id === "status-region") {
    const running = document.querySelector("#status-region .scraper-running");
    if (!running) {
      const btn = document.getElementById("run-btn");
      btn.disabled  = false;
      btn.className = "run-btn";
      btn.textContent = "▶ Run Scraper";
    }
  }
});