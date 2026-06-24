let all = [], filtered = [], sortCol = 'university', sortDir = 1, page = 1;
const PAGE = 50;
 
// ── Helpers ───────────────────────────────────────────────────────────────
 
function esc(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
 
// DB returns booleans; old JSON used "yes"/"no" strings — normalise both
function isFound(r) {
  return r.found === true || r.found === 'yes';
}
 
function isError(r) {
  return r.scrape_status === 'error';
}
 
// topics/languages/study_modes come as arrays from DB, strings from CSV
function toArray(val, sep = ';') {
  if (Array.isArray(val)) return val.map(v => String(v).trim()).filter(Boolean);
  if (!val) return [];
  return String(val).split(sep).map(v => v.trim()).filter(Boolean);
}
 
// ── Init ──────────────────────────────────────────────────────────────────
 
function init() {
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('main-area').classList.remove('hidden');
  buildSelects();
  updateStats();
  applyFilters();
}
 
function buildSelects() {
  const unis   = [...new Set(all.map(r => r.university).filter(Boolean))].sort();
  const topics = [...new Set(all.flatMap(r => toArray(r.topics)))].sort();
  const cities = [...new Set(all.map(r => r.city).filter(Boolean))].sort();
  fill('f-uni',   unis,   'All universities');
  fill('f-topic', topics, 'All topics');
  fill('f-city',  cities, 'All cities');
}
 
function fill(id, vals, placeholder) {
  const s = document.getElementById(id);
  s.innerHTML = `<option value="">${placeholder}</option>` +
    vals.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
}
 
function updateStats() {
  const n   = all.length;
  const f   = all.filter(isFound).length;
  const e   = all.filter(isError).length;
  const m   = n - f - e;
  const pct = n ? Math.round(f / n * 100) : 0;
 
  document.getElementById('s-total').textContent   = n;
  document.getElementById('s-found').textContent   = f;
  document.getElementById('s-missing').textContent = m;
  document.getElementById('s-errors').textContent  = e;
  document.getElementById('s-pct').textContent     = pct + '%';
  document.getElementById('cb-pct').textContent    = pct + '%';
  document.getElementById('cb-f').style.width = (n ? f / n * 100 : 0) + '%';
  document.getElementById('cb-m').style.width = (n ? m / n * 100 : 0) + '%';
  document.getElementById('cb-e').style.width = (n ? e / n * 100 : 0) + '%';
}
 
// ── Filters & sort ────────────────────────────────────────────────────────
 
function applyFilters() {
  const q  = document.getElementById('q').value.toLowerCase();
  const fs = document.getElementById('f-status').value;
  const fu = document.getElementById('f-uni').value;
  const ft = document.getElementById('f-topic').value;
  const fc = document.getElementById('f-city').value;
 
  filtered = all.filter(r => {
    const hay = [r.name_en, r.name_gr, r.university, r.department, r.city, r.notes, r.deadline]
      .join(' ').toLowerCase();
    if (q  && !hay.includes(q))      return false;
    if (fu && r.university !== fu)   return false;
    if (fc && r.city !== fc)         return false;
    if (ft && !toArray(r.topics).includes(ft)) return false;
 
    if (fs) {
      if (fs === 'found'   && !isFound(r))                  return false;
      if (fs === 'missing' && (isFound(r) || isError(r)))   return false;
      if (fs === 'error'   && !isError(r))                  return false;
      if (['open','closed','rolling','coming_soon','not_mentioned'].includes(fs)
          && r.application_status !== fs)                   return false;
    }
    return true;
  });
 
  filtered.sort((a, b) => {
    const va = (a[sortCol] || '').toString().toLowerCase();
    const vb = (b[sortCol] || '').toString().toLowerCase();
    return va < vb ? -sortDir : va > vb ? sortDir : 0;
  });
 
  page = 1;
  render();
}
 
// ── Render ────────────────────────────────────────────────────────────────
 
function render() {
  const start  = (page - 1) * PAGE;
  const slice  = filtered.slice(start, start + PAGE);
  const tbody  = document.getElementById('tbody');
  const empty  = document.getElementById('empty');
 
  document.getElementById('count').textContent = filtered.length + ' results';
 
  if (!filtered.length) {
    tbody.innerHTML = '';
    empty.classList.remove('hidden');
    document.getElementById('pag').innerHTML = '';
    return;
  }
  empty.classList.add('hidden');
 
  tbody.innerHTML = slice.map(r => {
    // Status badge
    const st = isError(r)         ? 'error'
             : !isFound(r)        ? 'missing'
             : r.application_status === 'open'       ? 'open'
             : r.application_status === 'closed'     ? 'closed'
             : r.application_status === 'rolling'    ? 'rolling'
             : r.application_status === 'coming_soon'? 'coming'
             : 'found';
 
    const stLabel = {
      error: 'Error', missing: 'No dates', open: 'Open',
      closed: 'Closed', rolling: 'Rolling', coming: 'Coming soon', found: 'Found'
    }[st] || st;
 
    // Topics — array from DB
    const topicList = toArray(r.topics);
    const topicTags = topicList.slice(0, 2)
      .map(t => `<span class="ptag ptag-topic">${esc(t)}</span>`).join('');
 
    // Apply link
    const applyLink = r.apply_url
      ? `<a href="${esc(r.apply_url)}" target="_blank" title="${esc(r.apply_url)}">Apply →</a>`
      : r.programme_url
      ? `<a href="${esc(r.programme_url)}" target="_blank">Website →</a>`
      : '<span style="color:#ddd">—</span>';

    const atsigLink = r.atsig_url
      ? `<a class="btn" style="font-size:12px" href="${esc(r.atsig_url)}" target="_blank">Edit</a>`
      : '<span style="color:#ddd">—</span>';
 
    const tuitionCls = r.tuition && r.tuition !== 'Free' ? 'paid' : '';
 
    const deadlineHtml = r.deadline
      ? `<span class="date-val has-date">${esc(r.deadline)}</span>`
      : `<span class="date-val no-date">—</span>`;
 
    const openHtml = r.open_date
      ? `<span class="date-val has-date">${esc(r.open_date)}</span>`
      : `<span class="date-val no-date">—</span>`;
 
    return `<tr>
      <td>
        <div class="uni-name">${esc(r.university)}</div>
        <div class="uni-dept" title="${esc(r.department)}">${esc(r.department)}</div>
        <span class="city-tag">${esc(r.city)}</span>
      </td>
      <td>
        <div class="prog-name">${esc(r.name_en)}</div>
        <div class="prog-tags">
          ${topicTags}
          ${r.ects     ? `<span class="ptag">${esc(r.ects)} ECTS</span>`     : ''}
          ${r.semesters? `<span class="ptag">${esc(r.semesters)} sem</span>` : ''}
        </div>
      </td>
      <td class="date-cell">${openHtml}</td>
      <td class="date-cell">${deadlineHtml}</td>
      <td style="font-size:11px;color:#bbb;white-space:nowrap">${esc(r.intake) || '—'}</td>
      <td><span class="badge b-${st}">${stLabel}</span></td>
      <td class="tuition ${tuitionCls}">${esc(r.tuition) || '—'}</td>
      <td class="apply-link">${applyLink}</td>
      <td class="notes-cell">${esc(r.notes) || ''}</td>
      <td class="apply-link">${atsigLink}</td>
    </tr>`;
  }).join('');
 
  renderPag();
}
 
function renderPag() {
  const tot = Math.ceil(filtered.length / PAGE);
  const pag = document.getElementById('pag');
  if (tot <= 1) { pag.innerHTML = ''; return; }
 
  let h = `<button class="pg" onclick="goPage(${page - 1})" ${page === 1 ? 'disabled' : ''}>← Prev</button>`;
  for (let i = 1; i <= tot; i++) {
    if (i === 1 || i === tot || Math.abs(i - page) <= 2)
      h += `<button class="pg${i === page ? ' on' : ''}" onclick="goPage(${i})">${i}</button>`;
    else if (Math.abs(i - page) === 3)
      h += `<span class="pg-dots">…</span>`;
  }
  h += `<button class="pg" onclick="goPage(${page + 1})" ${page === tot ? 'disabled' : ''}>Next →</button>`;
  pag.innerHTML = h;
}
 
window.goPage = function(n) {
  const tot = Math.ceil(filtered.length / PAGE);
  if (n < 1 || n > tot) return;
  page = n;
  render();
  document.querySelector('.tbl-wrap').scrollIntoView({ behavior: 'smooth' });
};
 
// ── Export ────────────────────────────────────────────────────────────────
 
function exportCSV() {
  if (!filtered.length) return;
  const keys = Object.keys(filtered[0]);
  const rows = [
    keys.join(','),
    ...filtered.map(r => keys.map(k => `"${(r[k] || '').toString().replace(/"/g, '""')}"`).join(','))
  ];
  const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'msc_deadlines.csv';
  a.click();
}

function exportJSON() {
  if (!filtered.length) return;
  const blob = new Blob([JSON.stringify(filtered, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'msc_deadlines.json';
  a.click();
}
 
// ── Event listeners ───────────────────────────────────────────────────────
 
document.getElementById('q').addEventListener('input', applyFilters);
['f-status', 'f-uni', 'f-topic', 'f-city'].forEach(id =>
  document.getElementById(id).addEventListener('change', applyFilters)
);
document.getElementById('f-sort').addEventListener('change', e => {
  sortCol = e.target.value;
  applyFilters();
});
document.getElementById('export-btn').addEventListener('click', exportCSV);
document.getElementById('export-json-btn').addEventListener('click', exportJSON);
 
document.querySelectorAll('thead th[data-col]').forEach(th => {
  th.addEventListener('click', () => {
    const col = th.dataset.col;
    if (sortCol === col) sortDir *= -1;
    else { sortCol = col; sortDir = 1; }
    document.querySelectorAll('thead th').forEach(t => t.classList.remove('asc', 'desc'));
    th.classList.add(sortDir === 1 ? 'asc' : 'desc');
    document.getElementById('f-sort').value = col;
    applyFilters();
  });
});
 
// ── Load from DB ──────────────────────────────────────────────────────────
 
async function loadFromDB() {
  try {
    const response = await fetch('/data/programmes/');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    all = data.data;
    init();
  } catch (err) {
    document.getElementById('loading').classList.add('hidden');
    const es = document.getElementById('error-state');
    es.style.display = 'flex';
    document.getElementById('error-detail').textContent = err.message;
  }
}
 
loadFromDB();