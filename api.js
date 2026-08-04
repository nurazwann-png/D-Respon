// D-Respon API layer — calls FastAPI backend, falls back to localStorage
const API_BASE = 'https://api-dot-prestij-nurazwann-smartassist.as.r.appspot.com';

let _idToken = null;
let _tokenExpiry = 0;  // Unix timestamp (ms)
let _refreshPending = false;

function setApiToken(token) {
  _idToken = token;
  // Google ID tokens expire in 1 hour; set expiry 5 min early to refresh proactively
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g,'+').replace(/_/g,'/')));
    _tokenExpiry = (payload.exp * 1000) - 5 * 60 * 1000;
  } catch(e) {
    _tokenExpiry = Date.now() + 55 * 60 * 1000;
  }
}

function isTokenExpired() {
  return _tokenExpiry > 0 && Date.now() > _tokenExpiry;
}

// Trigger silent Google token refresh via One Tap prompt
function _requestTokenRefresh() {
  if (_refreshPending) return;
  _refreshPending = true;
  if (window.google && window.google.accounts) {
    google.accounts.id.prompt(notification => {
      _refreshPending = false;
      if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
        // Silent refresh not possible — show re-login modal
        document.dispatchEvent(new CustomEvent('drTokenExpired'));
      }
    });
  } else {
    _refreshPending = false;
    document.dispatchEvent(new CustomEvent('drTokenExpired'));
  }
}

async function apiFetch(path, opts = {}) {
  if (!_idToken) throw new Error('Tiada token');
  if (isTokenExpired()) {
    _requestTokenRefresh();
    throw new Error('Token luput — sila log masuk semula');
  }
  const res = await fetch(API_BASE + path, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + _idToken,
      ...(opts.headers || {}),
    },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (res.status === 401) {
    _requestTokenRefresh();
    throw new Error('Sesi tamat — sila log masuk semula');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

// ── Polling for real-time sync ───────────────────────────────────────────────
let _pollTimer = null;
const POLL_INTERVAL = 60000; // 60 saat

function startPolling() {
  stopPolling();
  _pollTimer = setInterval(async () => {
    if (!_idToken || isTokenExpired()) return;
    if (document.visibilityState === 'hidden') return;
    try {
      const [remoteComplaints, remoteLogs] = await Promise.all([
        Api.getComplaints(),
        Api.getLogKerja(),
      ]);
      let changed = false;
      if (JSON.stringify(remoteComplaints) !== JSON.stringify(COMPLAINTS)) {
        COMPLAINTS.length = 0;
        remoteComplaints.forEach(c => COMPLAINTS.push(c));
        changed = true;
      }
      if (JSON.stringify(remoteLogs) !== JSON.stringify(LOG_KERJA)) {
        LOG_KERJA.length = 0;
        remoteLogs.forEach(l => LOG_KERJA.push(l));
        changed = true;
      }
      if (changed) {
        if (typeof filterComplaints === 'function') filterComplaints();
        if (typeof renderDashboard === 'function') renderDashboard();
        if (typeof showToast === 'function') showToast('Data dikemas kini secara automatik.', 'info', 2000);
      }
    } catch(e) { /* senyap — jangan ganggu pengguna */ }
  }, POLL_INTERVAL);
}

function stopPolling() {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
}

// ── Complaints ──────────────────────────────────────────────────────────────
const Api = {
  async getComplaints()          { return apiFetch('/api/complaints'); },
  async createComplaint(c)       { return apiFetch('/api/complaints', { method: 'POST', body: c }); },
  async updateComplaint(id, data){ return apiFetch(`/api/complaints/${id}`, { method: 'PUT', body: data }); },
  async deleteComplaint(id)      { return apiFetch(`/api/complaints/${id}`, { method: 'DELETE' }); },

  // Log Kerja
  async getLogKerja()            { return apiFetch('/api/log-kerja'); },
  async createLogKerja(entry)    { return apiFetch('/api/log-kerja', { method: 'POST', body: entry }); },

  // Audit Trail
  async getAudit()               { return apiFetch('/api/audit'); },
  async createAudit(entry)       { return apiFetch('/api/audit', { method: 'POST', body: entry }); },

  // Semak State
  async getSemak(kesId)          { return apiFetch(`/api/semak/${kesId}`); },
  async updateSemak(kesId, items){ return apiFetch(`/api/semak/${kesId}`, { method: 'PUT', body: { kes_id: kesId, checked_items: items } }); },

  // Bulk sync from localStorage → DB (run once on first login)
  async syncFromLocalStorage() {
    try {
      const complaints  = JSON.parse(localStorage.getItem('drComplaints') || '[]');
      const logKerja    = JSON.parse(localStorage.getItem('drLogKerja') || '[]');
      const auditRaw    = JSON.parse(localStorage.getItem('drAuditTrail') || '[]');
      const semakRaw    = JSON.parse(localStorage.getItem('drSemakState') || '{}');
      const counter     = parseInt(localStorage.getItem('drAduanCounter') || '0');

      const semakState = {};
      Object.keys(semakRaw).forEach(k => {
        semakState[k] = Array.isArray(semakRaw[k]) ? semakRaw[k] : [...(semakRaw[k] || [])];
      });

      const addId = arr => arr.map(x => ({ ...x, id: x.id || crypto.randomUUID() }));

      await apiFetch('/api/sync', {
        method: 'POST',
        body: {
          complaints: addId(complaints),
          log_kerja:  addId(logKerja),
          audit_trail: addId(auditRaw),
          semak_state: semakState,
          aduan_counter: counter,
        },
      });
      localStorage.setItem('drSyncDone', '1');
      return true;
    } catch (e) {
      console.warn('Sync gagal:', e.message);
      return false;
    }
  },
};
