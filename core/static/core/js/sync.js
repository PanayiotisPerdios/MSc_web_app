function getCookie(name) {
  const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return match ? match.pop() : '';
}
const csrftoken = getCookie('csrftoken');

document.getElementById("sync-btn").addEventListener("click", async () => {

    const btn = document.getElementById("sync-btn");
    const status = document.getElementById("sync-status");

    btn.disabled = true;
    btn.classList.add("syncing");

    btn.textContent = "⟳ Synchronizing...";
    status.textContent = "Fetching programmes from API...";

    try {

        const response = await fetch("/data/sync_programmes/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken
            }
        });

        const data = await response.json();

        btn.classList.remove("syncing");
        btn.classList.add("done");

        btn.textContent = "✓ Synchronization Complete";

        status.textContent =
            `Created: ${data.sync.created} | Updated: ${data.sync.updated} | Skipped ${data.sync.skipped}| Total: ${data.sync.total}`;

    } catch (err) {

        console.error(err);

        btn.classList.remove("syncing");

        btn.textContent = "Sync Failed";
        status.textContent = "An error occurred during synchronization.";

    } finally {

        setTimeout(() => {
            btn.disabled = false;

            btn.classList.remove("done");

            btn.textContent = "↻ Synchronize Programmes";
        }, 3000);

    }

});