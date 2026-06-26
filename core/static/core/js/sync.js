const btn = document.getElementById("sync-btn");

document.body.addEventListener("htmx:beforeRequest", e => {
  if (e.target !== btn) return;
  btn.classList.add("syncing");
  btn.querySelector("span") && (btn.querySelector("span").textContent = "⟳ Synchronizing...");
  btn.childNodes.forEach(n => { if (n.nodeType === 3) n.textContent = "⟳ Synchronizing..."; });
  document.getElementById("sync-status").textContent = "Synchronizing…";
});

document.body.addEventListener("htmx:afterRequest", e => {
  if (e.target !== btn) return;
  btn.classList.remove("syncing");
  if (e.detail.successful) {
    btn.classList.add("done");
    btn.childNodes.forEach(n => { if (n.nodeType === 3) n.textContent = "✓ Synchronization Complete"; });
    document.getElementById("sync-status").textContent = "Sync complete";
  } else {
    btn.childNodes.forEach(n => { if (n.nodeType === 3) n.textContent = "✕ Sync Failed"; });
    document.getElementById("sync-status").textContent = "Sync failed";
  }
  setTimeout(() => {
    btn.classList.remove("done");
    btn.childNodes.forEach(n => { if (n.nodeType === 3) n.textContent = "↻ Synchronize Programmes"; });
    document.getElementById("sync-status").textContent = "Ready to synchronize";
  }, 3000);
});

document.body.addEventListener("htmx:configRequest", e => {
  e.detail.headers["X-CSRFToken"] = getCookie("csrftoken");
});

function getCookie(name) {
  const match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
  return match ? match.pop() : "";
}