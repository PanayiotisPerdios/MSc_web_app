const btn            = document.getElementById('run-btn');
const statusBar      = document.getElementById('status-bar');
const spinner        = document.getElementById('spinner');
const statusTxt      = document.getElementById('status-text');
const elapsedEl      = document.getElementById('elapsed');
const statsEl        = document.getElementById('result-stats');
const logWrap        = document.getElementById('log-wrap');
const logBox         = document.getElementById('log-box');
const resultsToolbar = document.getElementById('results-toolbar');
const resultsWrap    = document.getElementById('results-wrap');
const resultsBody    = document.getElementById('results-body');
const btnResults     = document.getElementById('btn-results');
const resultsFilter  = document.getElementById('results-filter');
const resultsCount   = document.getElementById('results-count');
 
function getCookie(name) {
  const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return match ? match.pop() : '';
}
const csrftoken = getCookie('csrftoken');
 
let timer        = null;
let startTime    = null;
let logLineCount = 0;
let allRows      = [];
 
function startTimer() {
  startTime = Date.now();
  timer = setInterval(() => {
    const s = Math.floor((Date.now() - startTime) / 1000);
    const m = Math.floor(s / 60);
    elapsedEl.textContent = m > 0 ? `${m}m ${s % 60}s elapsed` : `${s}s elapsed`;
  }, 1000);
}
 
function stopTimer() {
  clearInterval(timer);
}
 
function setStatus(state, text) {
  statusBar.className   = 'visible ' + state;
  spinner.className     = 'spinner ' + state;
  statusTxt.className   = state;
  statusTxt.textContent = text;
}
 
function appendLog(lines) {
  lines.forEach(line => {
    if (!line.trim()) return;
    const div = document.createElement('div');
    if      (line.startsWith('CREATED'))           div.className = 'log-created';
    else if (line.startsWith('UPDATED'))           div.className = 'log-updated';
    else if (line.startsWith('SKIPPED'))           div.className = 'log-skipped';
    else if (line.toLowerCase().includes('error')) div.className = 'log-error';
    div.textContent = line;
    logBox.appendChild(div);
  });
  logBox.scrollTop = logBox.scrollHeight;
}
 
function statusBadge(status) {
  const s = (status || '').toLowerCase();
  if (s === 'open')        return '<span class="badge badge-open">Open</span>';
  if (s === 'closed')      return '<span class="badge badge-closed">Closed</span>';
  if (s === 'rolling')     return '<span class="badge badge-rolling">Rolling</span>';
  if (s === 'coming_soon') return '<span class="badge badge-other">Coming soon</span>';
  return '<span class="badge badge-other">—</span>';
}
 
function foundBadge(found, scrape_status) {
  if (scrape_status === 'error') return '<span class="badge badge-error">Error</span>';
  if (found === 'yes')           return '<span class="badge badge-found">Found</span>';
  return '<span class="badge badge-missing">Missing</span>';
}
 
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
 
function renderResults(rows) {
  resultsBody.innerHTML = '';
  rows.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <div class="cell-programme">${escHtml(r.name_en || '—')}</div>
        <div class="cell-uni">${escHtml(r.university || '')}</div>
      </td>
      <td class="cell-date ${r.open_date ? '' : 'empty'}">${escHtml(r.open_date || '—')}</td>
      <td class="cell-date ${r.deadline  ? '' : 'empty'}">${escHtml(r.deadline  || '—')}</td>
      <td class="cell-date ${r.intake    ? '' : 'empty'}">${escHtml(r.intake    || '—')}</td>
      <td>${statusBadge(r.status)}</td>
      <td>${r.apply_url ? `<a class="apply-link" href="${escHtml(r.apply_url)}" target="_blank" rel="noopener">Apply ↗</a>` : '<span style="color:#ccc">—</span>'}</td>
      <td>${r.atsig_url ? `<a class="apply-link" href="${escHtml(r.atsig_url)}" target="_blank" rel="noopener">Edit ↗</a>`  : '<span style="color:#ccc">—</span>'}</td>
      <td>${foundBadge(r.found, r.scrape_status)}</td>
    `;
    resultsBody.appendChild(tr);
  });
  resultsCount.textContent = `${rows.length} programme${rows.length !== 1 ? 's' : ''}`;
}
 
function filterResults(query) {
  if (!query.trim()) return renderResults(allRows);
  const q = query.toLowerCase();
  renderResults(allRows.filter(r =>
    (r.name_en    || '').toLowerCase().includes(q) ||
    (r.university || '').toLowerCase().includes(q)
  ));
}
 
function showStats(result) {
  document.getElementById('r-total').textContent   = result.scope_total   ?? result.total   ?? '—';
  document.getElementById('r-found').textContent   = result.scope_found   ?? result.created ?? '—';
  document.getElementById('r-skipped').textContent = result.scope_skipped ?? result.skipped ?? '—';
  document.getElementById('r-errors').textContent  = result.scope_errors  ?? 0;
  statsEl.classList.add('visible');
}
 
async function pollLogs() {
  try {
    const r    = await fetch(`/data/scraper_logs/?since=${logLineCount}`);
    const data = await r.json();
    if (data.lines?.length) {
      appendLog(data.lines);
      logLineCount = data.total;
    }
  } catch (e) {}
}
 
btn.addEventListener('click', async () => {
  const config = {
    model:            document.querySelector('[name="model"]').value,
    workers:          Number(document.querySelector('[name="workers"]').value),
    limit:            document.querySelector('[name="limit"]').value
                        ? Number(document.querySelector('[name="limit"]').value) : null,
    offset:           Number(document.querySelector('[name="offset"]').value),
    ids:              document.querySelector('[name="ids"]').value || null,
    resume:           document.querySelector('[name="resume"]').checked,
    pass2_only:       document.querySelector('[name="pass2_only"]').checked,
    include_archived: document.querySelector('[name="include_archived"]').checked,
    missing_only:     document.querySelector('[name="missing_only"]').checked,
  };
 
  btn.disabled = true;
  btn.className = 'run-btn running';
  btn.textContent = '⟳ Running…';
  logBox.innerHTML = '';
  logLineCount = 0;
  allRows = [];
  statsEl.classList.remove('visible');
  resultsToolbar.classList.remove('visible');
  resultsWrap.classList.remove('visible');
  logWrap.classList.add('visible');
  setStatus('running', 'Syncing with API & running scraper…');
  startTimer();
 
  try {
    const res = await fetch('/data/post_scraper/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      body: JSON.stringify(config),
    });
 
    const startData = await res.json();
    if (startData.status !== 'started') {
      stopTimer();
      setStatus('failed', startData.message || 'Failed to start');
      btn.disabled = false;
      btn.className = 'run-btn';
      btn.textContent = '▶ Run Scraper';
      return;
    }
 
    const poll = setInterval(async () => {
      await pollLogs();
 
      try {
        const s = await fetch('/data/scraper_status/').then(r => r.json());
        if (!s.running) {
          clearInterval(poll);
          await pollLogs();
          stopTimer();
 
          if (s.error) {
            setStatus('failed', `Error: ${s.error}`);
            btn.className = 'run-btn failed';
            btn.textContent = '✕ Failed';
          } else {
            const result = s.result || {};
            setStatus('done', `Done — ${result.scope_total ?? result.total ?? 0} programmes processed`);
            btn.className = 'run-btn done';
            btn.textContent = '✓ Complete';
            showStats(result);
            if (result.changes?.length) appendLog(result.changes);
 
            if (result.rows?.length) {
              allRows = result.rows;
              resultsToolbar.classList.add('visible');
              resultsFilter.value = '';
            }
          }
 
          setTimeout(() => {
            btn.disabled = false;
            btn.className = 'run-btn';
            btn.textContent = '▶ Run Scraper';
          }, 4000);
        }
      } catch (e) {
        // status endpoint temporarily unreachable, keep polling
      }
    }, 2000);
 
  } catch (err) {
    stopTimer();
    setStatus('failed', `Request failed: ${err.message}`);
    btn.className = 'run-btn failed';
    btn.textContent = '✕ Failed';
    appendLog([`ERROR: ${err.message}`]);
    setTimeout(() => {
      btn.disabled = false;
      btn.className = 'run-btn';
      btn.textContent = '▶ Run Scraper';
    }, 4000);
  }
});
 
btnResults.addEventListener('click', () => {
  const open = resultsWrap.classList.contains('visible');
  if (open) {
    resultsWrap.classList.remove('visible');
    btnResults.textContent = 'Show Results';
  } else {
    renderResults(allRows);
    resultsWrap.classList.add('visible');
    btnResults.textContent = 'Hide Results';
    resultsWrap.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
});
 
resultsFilter.addEventListener('input', () => filterResults(resultsFilter.value));
 
document.getElementById('log-clear').addEventListener('click', () => {
  logBox.innerHTML = '';
});