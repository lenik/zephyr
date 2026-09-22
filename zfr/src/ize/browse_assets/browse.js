const MARK = { default: ' ', always: '*', ignored: '-' };
const CYCLE = ['default', 'ignored', 'always'];
const STATE_TITLE = {
  default: 'default (use ize.options)',
  always: 'always — force enable (override -u)',
  ignored: 'ignored — skip this rule',
};

let STATE = null;
let currentId = null;

function showAll() {
  return document.getElementById('show-all').checked;
}

function visibleRules() {
  const all = STATE.rules || [];
  if (showAll()) return all;
  return all.filter(r => !r.nop && (r.edit_count || 0) > 0);
}

function nextState(cur) {
  const i = CYCLE.indexOf(cur);
  return CYCLE[((i < 0 ? 0 : i) + 1) % CYCLE.length];
}

async function loadData(refresh) {
  const el = document.getElementById('loading');
  el.hidden = false;
  try {
    const q = refresh ? '?refresh=1' : '';
    const r = await fetch('/api/data' + q);
    STATE = await r.json();
    const n = (STATE.rules || []).length;
    const v = visibleRules().length;
    document.getElementById('meta').textContent =
      'zfr ize — ' + (STATE.root || '') + '  lang=' + (STATE.lang || '') +
      '  (' + v + (v === n ? '' : '/' + n) + ' rules)';
    renderRules();
    const vis = visibleRules();
    if (vis.length) {
      const keep = currentId && vis.find(x => x.rule_id === currentId);
      selectRule(keep ? currentId : vis[0].rule_id);
    } else {
      currentId = null;
      document.getElementById('title').textContent = '';
      document.getElementById('docs').textContent = '';
      document.getElementById('diffs').innerHTML =
        '<p class="loading">No pending edits' +
        (showAll() ? '.' : ' (enable Show All to see nop rules).') + '</p>';
      document.getElementById('comments').textContent = '';
    }
  } finally {
    el.hidden = true;
  }
}

function renderRules() {
  const box = document.getElementById('rules');
  box.innerHTML = '';
  for (const rule of visibleRules()) {
    const st = rule.state || 'default';
    const mark = MARK[st] ?? ' ';
    const row = document.createElement('div');
    row.className = 'rule' + (rule.rule_id === currentId ? ' active' : '');
    row.dataset.id = rule.rule_id;

    const tri = document.createElement('button');
    tri.type = 'button';
    tri.className = 'mark ' + st;
    tri.dataset.rid = rule.rule_id;
    tri.title = STATE_TITLE[st] || st;
    tri.setAttribute('aria-label', 'Rule state: ' + st);
    tri.textContent = '[' + mark + ']';
    tri.onclick = (ev) => {
      ev.stopPropagation();
      cycleRuleState(rule.rule_id);
    };

    const body = document.createElement('button');
    body.type = 'button';
    body.className = 'rule-body';
    body.innerHTML =
      '<span class="id">' + esc(rule.rule_id) + '</span>' +
      '<span class="code">' + esc(rule.code) + '</span>' +
      '<span class="n">' + (rule.edit_count || 0) + '</span>';
    body.onclick = () => selectRule(rule.rule_id);

    row.appendChild(tri);
    row.appendChild(body);
    box.appendChild(row);
  }
}

function patchLocalState(rid, state) {
  const rule = (STATE.rules || []).find(r => r.rule_id === rid);
  if (rule) rule.state = state;
  renderRules();
}

async function cycleRuleState(rid) {
  const rule = (STATE.rules || []).find(r => r.rule_id === rid);
  if (!rule) return;
  const cur = rule.state || 'default';
  const next = nextState(cur);
  patchLocalState(rid, next);
  try {
    const r = await fetch('/api/rule-state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rule_id: rid, state: next }),
    });
    const j = await r.json();
    if (!j.ok) {
      patchLocalState(rid, cur);
      alert(j.error || 'rule-state failed');
    }
  } catch (err) {
    patchLocalState(rid, cur);
    alert(String(err));
  }
}

function selectRule(id) {
  currentId = id;
  const rule = (STATE.rules || []).find(r => r.rule_id === id);
  if (!rule) return;
  renderRules();
  const st = rule.state || 'default';
  document.getElementById('title').textContent =
    '[' + (MARK[st] ?? ' ') + '] ' +
    rule.rule_id + '  ' + rule.code + ' — ' + (rule.title || '');
  const docs = rule.docs && rule.docs.sections
    ? rule.docs.sections.map(s => '## ' + s.title + '\n' + s.body).join('\n\n')
    : '';
  document.getElementById('docs').textContent = docs;
  const diffs = document.getElementById('diffs');
  diffs.innerHTML = (rule.diffs || []).map(d =>
    '<div><strong>' + esc(d.path) + '</strong> (' + esc(d.kind) + ') ' +
    esc(d.detail || '') + d.diff_html + '</div>'
  ).join('') || '<p class="loading">No pending edits for this rule.</p>';
  const c = rule.comments || {};
  document.getElementById('comments').textContent =
    [c.project, c.user].filter(Boolean).join('\n---\n') || '';
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

document.getElementById('refresh').onclick = () => loadData(true);
document.getElementById('show-all').onchange = () => {
  renderRules();
  const vis = visibleRules();
  if (!vis.length) {
    currentId = null;
    document.getElementById('title').textContent = '';
    document.getElementById('diffs').innerHTML =
      '<p class="loading">No pending edits (enable Show All to see nop rules).</p>';
    return;
  }
  if (!vis.find(r => r.rule_id === currentId)) {
    selectRule(vis[0].rule_id);
  }
};
document.getElementById('apply-all').onclick = async () => {
  await fetch('/api/apply-all', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  });
  await loadData(true);
};
document.getElementById('apply-one').onclick = async () => {
  if (!currentId) return;
  await fetch('/api/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: currentId }),
  });
  await loadData(true);
};
document.getElementById('comment-submit').onclick = async () => {
  const text = document.getElementById('comment').value;
  if (!currentId || !text.trim()) return;
  await fetch('/api/comment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      rule_id: currentId,
      text,
      project_only: document.getElementById('proj-only').checked,
    }),
  });
  document.getElementById('comment').value = '';
  await loadData(true);
};

loadData(false);
