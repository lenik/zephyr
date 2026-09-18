let STATE = null;
let UI = {};
const izeCache = {};
const expanded = new Set();
const commenting = new Set();
let sortBy = 'id';
let loading = false;

const MARK = { default: ' ', always: '*', ignored: '-' };
const CYCLE = ['default', 'ignored', 'always'];
const SEV_ORDER = { error: 0, warn: 1, note: 2, ok: 3 };

function theme() {
  return document.documentElement.getAttribute('data-theme') || 'dark';
}
function setTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  try { localStorage.setItem('zfr-lint-theme', t); } catch (e) {}
  const btn = document.getElementById('theme');
  if (btn && UI.theme_light) {
    btn.textContent = t === 'dark' ? UI.theme_light : UI.theme_dark;
  }
}
(function initTheme() {
  let t = 'dark';
  try { t = localStorage.getItem('zfr-lint-theme') || t; } catch (e) {}
  document.documentElement.setAttribute('data-theme', t);
})();

function pickUi(lang) {
  const maps = STATE.ui_maps || {};
  if (maps[lang]) return maps[lang];
  const base = String(lang || 'en').split('_')[0];
  for (const k of Object.keys(maps)) {
    if (k === base || k.startsWith(base + '_')) return maps[k];
  }
  return maps.en || STATE.ui || {};
}

function setLoading(on) {
  loading = !!on;
  const el = document.getElementById('loading');
  if (el) {
    el.hidden = !loading;
    el.textContent = loading ? (UI.running || '…') : '';
  }
  const refresh = document.getElementById('refresh');
  if (refresh) refresh.disabled = loading;
}

function setUiLang(lang) {
  STATE.ui_lang = lang;
  try { localStorage.setItem('zfr-lint-lang', lang); } catch (e) {}
  // Chrome + markdown docs only — do not re-lint (use Re-lint for that).
  return loadData(lang, { refresh: false });
}

async function loadData(lang, opts) {
  const refresh = !!(opts && opts.refresh);
  const params = new URLSearchParams();
  if (lang) params.set('lang', lang);
  if (refresh) params.set('refresh', '1');
  const q = params.toString() ? ('?' + params.toString()) : '';
  setLoading(true);
  try {
    const r = await fetch('/api/data' + q);
    STATE = await r.json();
    UI = pickUi(STATE.ui_lang || lang || 'en');
    document.documentElement.lang = STATE.ui_lang || lang || 'en';
    const sel = document.getElementById('locale');
    if (sel && STATE.ui_lang) sel.value = STATE.ui_lang;
    applyChrome();
    renderCards();
  } finally {
    setLoading(false);
  }
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function updateStatusbar() {
  const c = STATE.counts;
  const total = Math.max(1, c.error + c.warn + c.note + c.ok);
  const okp = 100 * c.ok / total;
  const wp = 100 * c.warn / total;
  const ep = 100 * c.error / total;
  document.getElementById('sb-ver').textContent = 'zfr ' + STATE.zfr_version;
  document.getElementById('sb-author').textContent = STATE.author || '';
  const bar = document.getElementById('sb-bar');
  bar.querySelector('.ok').style.width = okp + '%';
  bar.querySelector('.warn').style.width = wp + '%';
  bar.querySelector('.err').style.width = ep + '%';
  document.getElementById('sb-rates').textContent =
    UI.pass_rate + ' ' + Math.round(okp) + '% · warn ' + Math.round(wp) + '% · err ' + Math.round(ep) + '%';
}

function applyChrome() {
  document.title = (UI.title || 'zfr lint') + ' — ' + STATE.name;
  document.getElementById('meta').innerHTML =
    '<strong>' + esc(STATE.name) + '</strong> · ' + esc(STATE.root) +
    ' · ' + esc(STATE.lang) + '/' + esc(STATE.role);
  document.getElementById('lbl-show-all').textContent = UI.show_all;
  document.getElementById('refresh').textContent = UI.refresh;
  document.getElementById('empty-hint').textContent = UI.no_findings;
  document.getElementById('lbl-sort').textContent = UI.sort + ':';
  const sortSel = document.getElementById('sort');
  sortSel.innerHTML =
    '<option value="id">' + esc(UI.sort_id) + '</option>' +
    '<option value="status">' + esc(UI.sort_status) + '</option>' +
    '<option value="name">' + esc(UI.sort_name) + '</option>';
  sortSel.value = sortBy;
  document.getElementById('lbl-request').textContent = UI.request_new;
  document.getElementById('request-text').placeholder = UI.request_hint;
  document.getElementById('lbl-request-proj').textContent = UI.project_only;
  document.getElementById('request-submit').textContent = UI.submit;
  const reqExist = (STATE.new_requests || '');
  document.getElementById('request-existing').innerHTML = reqExist
    ? esc(reqExist) : '';
  document.getElementById('request-existing').style.display = reqExist ? '' : 'none';
  setTheme(theme());
  const sel = document.getElementById('locale');
  const locales = STATE.locales || Object.keys(STATE.ui_maps || {});
  sel.innerHTML = locales.map(L =>
    '<option value="' + esc(L) + '"' + (L === STATE.ui_lang ? ' selected' : '') + '>' + esc(L) + '</option>'
  ).join('');
  const c = STATE.counts;
  const failed = c.error > 0;
  document.getElementById('counts').innerHTML =
    '<span><strong class="sev-' + (failed ? 'error' : 'ok') + '">' +
    (failed ? 'FAIL' : 'PASS') + '</strong></span>' +
    '<span class="sev-error">' + esc(UI.errors) + '=' + c.error + '</span>' +
    '<span class="sev-warn">' + esc(UI.warnings) + '=' + c.warn + '</span>' +
    '<span class="sev-note">' + esc(UI.notes) + '=' + c.note + '</span>' +
    '<span class="sev-ok">' + esc(UI.ok) + '=' + c.ok + '</span>';
  updateStatusbar();
}

function sortedFindings() {
  const list = STATE.findings.slice();
  const byId = (a, b) =>
    String(a.rule_id).localeCompare(String(b.rule_id)) ||
    String(a.code).localeCompare(String(b.code));
  if (sortBy === 'status') {
    list.sort((a, b) =>
      (SEV_ORDER[a.severity] ?? 9) - (SEV_ORDER[b.severity] ?? 9) || byId(a, b)
    );
  } else if (sortBy === 'name') {
    list.sort((a, b) =>
      String(a.code).localeCompare(String(b.code)) || byId(a, b)
    );
  } else {
    list.sort(byId);
  }
  return list;
}

function renderCards() {
  const main = document.getElementById('main');
  main.innerHTML = sortedFindings().map((f, i) => cardHtml(f, i)).join('');
  applyShowAll();
  bindCards();
}

function docsHtml(docs) {
  const sections = (docs && docs.sections) || [];
  if (!sections.length) return '<p class="code">(no documentation)</p>';
  return sections.map(s =>
    '<h4>' + esc(s.title || '') + '</h4><p>' + esc(s.body || '') + '</p>'
  ).join('');
}

function cardHtml(f, i) {
  const loc = f.file ? (f.line ? f.file + ':' + f.line : f.file) : '';
  const st = f.rule_state || 'default';
  const mark = MARK[st] ?? ' ';
  const rid = f.rule_id;
  const open = expanded.has(rid);
  const cmtOpen = commenting.has(rid);
  const cached = izeCache[f.code];
  const result = cached
    ? (cached.ok ? '<span class="tick" title="ok">✓</span>' : '<span class="cross" title="err">✗</span>')
    : '';
  let actions = '';
  if (f.izeable) {
    actions = '<a href="#" class="act solve" data-code="' + esc(f.code) + '">' + esc(UI.solve) + '</a>';
    if (cached) {
      const showCls = cached.ok ? 'act show' : 'act bad show';
      actions += '<a href="#" class="' + showCls + '" data-code="' + esc(f.code) + '">' + esc(UI.show) + '</a>' + result;
    }
  }
  const fix = f.fix
    ? '<div class="fix"><strong>' + esc(UI.fix) + ':</strong> ' + esc(f.fix) + '</div>'
    : '';
  const existing =
    (f.comments && f.comments.project
      ? '<div><strong>project:</strong>\\n' + esc(f.comments.project) + '</div>' : '') +
    (f.comments && f.comments.user
      ? '<div><strong>user:</strong>\\n' + esc(f.comments.user) + '</div>' : '');

  const hide = (f.severity === 'ok' && !document.getElementById('show-all').checked)
    ? ' hidden' : '';

  let panel = '';
  if (open) {
    panel =
      '<tr class="panel-row' + hide + '" data-ok="' + (f.severity === 'ok' ? '1' : '0') +
      '" data-rid="' + esc(rid) + '"><td colspan="3">' +
      '<div class="docs">' + docsHtml(f.docs) + '</div>' +
      (existing && !cmtOpen ? '<div class="existing">' + existing + '</div>' : '') +
      (cmtOpen
        ? '<div class="comment-box">' +
          '<hr class="divider">' +
          (existing ? '<div class="existing">' + existing + '</div>' : '') +
          '<textarea data-rid="' + esc(rid) + '" placeholder="' + esc(UI.enter_comments) + '"></textarea>' +
          '<div class="row2">' +
          '<label><input type="checkbox" class="proj-only"> ' + esc(UI.project_only) + '</label>' +
          '<span>' +
          '<button type="button" class="submit-cmt" data-rid="' + esc(rid) + '">' + esc(UI.submit) + '</button> ' +
          '<span class="code cmt-status" data-rid="' + esc(rid) + '"></span>' +
          '</span></div></div>'
        : '<div class="panel-actions">' +
          '<button type="button" class="add-cmt" data-rid="' + esc(rid) + '">' + esc(UI.add_comment) + '</button>' +
          '</div>') +
      '</td></tr>';
  }

  return '<tr class="head' + hide + '" data-ok="' + (f.severity === 'ok' ? '1' : '0') +
    '" data-rid="' + esc(rid) + '">' +
    '<td class="col-main toggle-exp" data-rid="' + esc(rid) + '"><div class="head-left">' +
    '<span class="mark ' + esc(st) + '" data-rid="' + esc(rid) + '" title="' + esc(UI.rule_state) +
    '">[' + esc(mark) + ']</span>' +
    '<span class="sev-' + esc(f.severity) + '">' + esc(f.severity) + '</span>' +
    '<span class="rid">' + esc(rid) + '</span>' +
    '<span class="code">' + esc(f.code) + '</span>' +
    (f.docs && f.docs.title
      ? '<span class="short-title">' + esc(f.docs.title) + '</span>' : '') +
    (loc ? '<span class="loc">' + esc(loc) + '</span>' : '') +
    '</div></td>' +
    '<td class="col-act"><div class="head-right">' + actions + '</div></td>' +
    '<td class="col-exp"></td></tr>' +
    '<tr class="msg' + hide + '" data-ok="' + (f.severity === 'ok' ? '1' : '0') +
    '" data-rid="' + esc(rid) + '">' +
    '<td class="col-main toggle-exp" data-rid="' + esc(rid) + '"><div class="msg">' +
    esc(f.message) + '</div>' + fix + '</td>' +
    '<td class="col-act"></td>' +
    '<td class="col-exp"><button type="button" class="expand-btn" data-rid="' + esc(rid) +
    '" title="' + esc(UI.docs) + '">' + (open ? '▾' : '▸') + '</button></td></tr>' +
    panel;
}

function applyShowAll() {
  const show = document.getElementById('show-all').checked;
  document.querySelectorAll('#main tr').forEach(tr => {
    if (tr.dataset.ok === '1') tr.classList.toggle('hidden', !show);
  });
  const visible = [...document.querySelectorAll('#main tr.head')].filter(
    tr => !tr.classList.contains('hidden')
  );
  document.getElementById('empty-hint').hidden = visible.length > 0;
}

function toggleExpand(rid) {
  if (expanded.has(rid)) {
    expanded.delete(rid);
    commenting.delete(rid);
  } else {
    expanded.add(rid);
  }
  renderCards();
}

function patchRuleState(rid, state) {
  for (const f of STATE.findings) {
    if (f.rule_id === rid) f.rule_state = state;
  }
  renderCards();
}

function patchComments(rid, projectOnly, text) {
  const key = projectOnly ? 'project' : 'user';
  for (const f of STATE.findings) {
    if (f.rule_id !== rid) continue;
    if (!f.comments) f.comments = { project: '', user: '' };
    const prev = (f.comments[key] || '').replace(/\s+$/, '');
    f.comments[key] = prev ? (prev + '\\n\\n' + text + '\\n') : (text + '\\n');
  }
}

function bindCards() {
  document.querySelectorAll('.expand-btn').forEach(btn => {
    btn.onclick = (ev) => {
      ev.stopPropagation();
      toggleExpand(btn.dataset.rid);
    };
  });
  document.querySelectorAll('.toggle-exp').forEach(el => {
    el.onclick = (ev) => {
      if (ev.target.closest('.mark, a.act, button, input, textarea, label')) return;
      toggleExpand(el.dataset.rid);
    };
  });
  document.querySelectorAll('.add-cmt').forEach(btn => {
    btn.onclick = () => {
      commenting.add(btn.dataset.rid);
      expanded.add(btn.dataset.rid);
      renderCards();
      const ta = document.querySelector('textarea[data-rid="' + btn.dataset.rid + '"]');
      if (ta) ta.focus();
    };
  });
  document.querySelectorAll('a.solve').forEach(a => {
    a.onclick = async (ev) => {
      ev.preventDefault();
      const code = a.dataset.code;
      a.textContent = UI.running;
      try {
        const r = await fetch('/api/ize', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ code, lang: STATE.ui_lang }),
        });
        const j = await r.json();
        izeCache[code] = j;
        await loadData(STATE.ui_lang, { refresh: true });
      } catch (err) {
        alert(String(err));
        a.textContent = UI.solve;
      }
    };
  });
  document.querySelectorAll('a.show').forEach(a => {
    a.onclick = (ev) => {
      ev.preventDefault();
      const j = izeCache[a.dataset.code];
      if (!j) return;
      const modal = document.getElementById('modal');
      modal.hidden = false;
      modal.innerHTML = '<div class="modal-bg"><div class="modal"><header><strong>' +
        esc(UI.output) + '</strong><button type="button" id="modal-close">' + esc(UI.close) +
        '</button></header>' + (j.html || '') + '</div></div>';
      document.getElementById('modal-close').onclick = () => { modal.hidden = true; modal.innerHTML = ''; };
      modal.querySelector('.modal-bg').onclick = (e) => {
        if (e.target.classList.contains('modal-bg')) { modal.hidden = true; modal.innerHTML = ''; }
      };
    };
  });
  document.querySelectorAll('.mark').forEach(el => {
    el.onclick = async (ev) => {
      ev.stopPropagation();
      const rid = el.dataset.rid;
      const cur = el.classList.contains('always') ? 'always' :
        el.classList.contains('ignored') ? 'ignored' : 'default';
      const next = CYCLE[(CYCLE.indexOf(cur) + 1) % CYCLE.length];
      /* Optimistic UI — do not re-lint. */
      patchRuleState(rid, next);
      try {
        const r = await fetch('/api/rule-state', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ rule_id: rid, state: next }),
        });
        const j = await r.json();
        if (!j.ok) {
          patchRuleState(rid, cur);
          alert(j.error || 'rule-state failed');
        }
      } catch (err) {
        patchRuleState(rid, cur);
        alert(String(err));
      }
    };
  });
  document.querySelectorAll('.submit-cmt').forEach(btn => {
    btn.onclick = async () => {
      const rid = btn.dataset.rid;
      const row = btn.closest('tr');
      const ta = row.querySelector('textarea');
      const projOnly = !!(row.querySelector('.proj-only') && row.querySelector('.proj-only').checked);
      const text = ta.value.trim();
      if (!text) return;
      const r = await fetch('/api/comment', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ rule_id: rid, text, project_only: projOnly }),
      });
      const j = await r.json();
      const st = row.querySelector('.cmt-status[data-rid="' + rid + '"]');
      if (!j.ok) {
        if (st) st.textContent = j.error || 'error';
        return;
      }
      patchComments(rid, projOnly, text);
      commenting.delete(rid);
      if (st) st.textContent = UI.saved;
      renderCards();
    };
  });
}

document.getElementById('show-all').addEventListener('change', applyShowAll);
document.getElementById('sort').addEventListener('change', (e) => {
  sortBy = e.target.value || 'id';
  try { localStorage.setItem('zfr-lint-sort', sortBy); } catch (err) {}
  renderCards();
});
document.getElementById('locale').addEventListener('change', (e) => {
  setUiLang(e.target.value);
});
document.getElementById('refresh').addEventListener('click', () =>
  loadData(STATE.ui_lang, { refresh: true })
);
document.getElementById('theme').addEventListener('click', () => {
  setTheme(theme() === 'dark' ? 'light' : 'dark');
});
document.getElementById('request-submit').addEventListener('click', async () => {
  const ta = document.getElementById('request-text');
  const text = ta.value.trim();
  if (!text) return;
  const projOnly = document.getElementById('request-proj').checked;
  const st = document.getElementById('request-status');
  const r = await fetch('/api/comment', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ rule_id: 'NEW', text, project_only: projOnly }),
  });
  const j = await r.json();
  if (!j.ok) {
    st.textContent = j.error || 'error';
    return;
  }
  const prev = (STATE.new_requests || '').replace(/\s+$/, '');
  STATE.new_requests = prev ? (prev + '\\n\\n' + text + '\\n') : (text + '\\n');
  ta.value = '';
  st.textContent = UI.saved;
  document.getElementById('request-existing').textContent = STATE.new_requests;
  document.getElementById('request-existing').style.display = '';
});
try {
  const s = localStorage.getItem('zfr-lint-sort');
  if (s === 'id' || s === 'status' || s === 'name') sortBy = s;
} catch (e) {}
(function bootLang() {
  let lang = new URLSearchParams(location.search).get('lang');
  if (!lang) {
    try { lang = localStorage.getItem('zfr-lint-lang'); } catch (e) {}
  }
  if (!lang) lang = window.ZFR_BROWSE_DEFAULT_LANG || '';
  loadData(lang || 'en', { refresh: false });
})();
