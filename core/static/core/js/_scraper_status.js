  function filterRows(q) {
    const rows  = document.querySelectorAll("#results-body tr");
    const lower = q.toLowerCase().trim();
    let visible = 0;
    rows.forEach(tr => {
      const match = !lower
        || tr.dataset.name.includes(lower)
        || tr.dataset.uni.includes(lower);
      tr.style.display = match ? "" : "none";
      if (match) visible++;
    });
    document.getElementById("results-count").textContent =
      visible + " programme" + (visible !== 1 ? "s" : "");
  }