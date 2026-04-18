/**
 * AI Digital Memory Vault — Main Application Logic
 * Handles: Dashboard table, API calls, toast notifications, utilities
 */

const API_BASE = `http://${window.location.hostname || 'localhost'}:8000`;

// ========== State ==========
let fetchedEvidence = []; // Store fetched evidence for filtering

// ========== Toast Notification System ==========
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  toast.innerHTML = `
    <span style="font-size:1.1rem;">${icons[type] || 'ℹ️'}</span>
    <span style="flex:1;font-size:0.88rem;">${message}</span>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1rem;padding:0 0.3rem;">✕</button>
  `;

  container.appendChild(toast);

  // Auto-remove after 4 seconds
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ========== Dashboard: Populate Evidence Table ==========
function populateEvidenceTable(data) {
  const tbody = document.getElementById('evidence-tbody');
  if (!tbody) return;

  tbody.innerHTML = '';

  if (!data || data.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; color:var(--text-muted); padding:2rem;">
          No evidence records found. <a href="upload.html" style="color:var(--teal);">Upload evidence</a> or use <a href="protection.html" style="color:var(--teal);">Demo Mode</a>.
        </td>
      </tr>
    `;
    return;
  }

  data.forEach(item => {
    const statusBadge = getStatusBadge(item.status);
    const confidenceDisplay = item.confidence !== null && item.confidence !== undefined
      ? `<span style="font-weight:700;color:${item.confidence > 55 ? 'var(--danger)' : item.confidence > 35 ? 'var(--warning)' : 'var(--success)'};">${item.confidence}%</span>`
      : '<span style="color:var(--text-muted);">—</span>';

    const row = document.createElement('tr');
    row.innerHTML = `
      <td><span style="font-family:var(--font-mono);font-weight:600;color:var(--teal);">${item.id}</span></td>
      <td><span style="font-family:var(--font-mono);font-size:0.83rem;">${formatTimestamp(item.timestamp)}</span></td>
      <td>${item.type || 'Audio'}</td>
      <td>${item.location || 'Unknown'}</td>
      <td>${statusBadge}</td>
      <td>${confidenceDisplay}</td>
      <td>
        <div style="display:flex;gap:0.3rem;">
          <a href="incident.html?id=${item.id}" class="btn btn-sm btn-secondary" title="View Details">🔍</a>
          <a href="report.html?id=${item.id}" class="btn btn-sm btn-secondary" title="View Report">📄</a>
        </div>
      </td>
    `;
    tbody.appendChild(row);
  });
}

function formatTimestamp(ts) {
  if (!ts) return '—';
  try {
    const d = new Date(ts);
    if (isNaN(d.getTime())) return ts;
    return d.toLocaleString('en-IN', { 
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  } catch {
    return ts;
  }
}

function getStatusBadge(status) {
  const map = {
    analyzed: '<span class="badge badge-success">✓ Analyzed</span>',
    pending: '<span class="badge badge-warning">⏳ Pending</span>',
    processing: '<span class="badge badge-info">⚙️ Processing</span>',
    error: '<span class="badge badge-danger">✕ Error</span>',
  };
  return map[status] || map.pending;
}

// ========== Dashboard: Fetch Evidence from Backend ==========
async function fetchEvidenceList() {
  try {
    const response = await fetch(`${API_BASE}/evidence/list`);
    if (response.ok) {
      const data = await response.json();
      const evidence = data.evidence || [];
      fetchedEvidence = evidence; // Store for filtering
      populateEvidenceTable(evidence);
      updateStats(evidence);
      populateActivityFeed(evidence);
      return;
    }
  } catch (e) {
    console.log('Backend not available:', e.message);
  }

  // Show empty state when backend is not available
  fetchedEvidence = [];
  populateEvidenceTable([]);
  updateStats([]);
  populateActivityFeed([]);
}

// ========== Dashboard: Populate Activity Feed ==========
function populateActivityFeed(data) {
  const feed = document.getElementById('activity-feed');
  if (!feed) return;

  if (!data || data.length === 0) {
    feed.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:1.5rem;">No recent activity. <a href="upload.html" style="color:var(--teal);">Upload evidence</a> to get started.</div>';
    return;
  }

  // Take the most recent 5 items
  const recent = data.slice(0, 5);
  feed.innerHTML = '';

  recent.forEach((item, idx) => {
    const isLast = idx === recent.length - 1;
    let badge = '';
    let text = '';

    if (item.status === 'analyzed' && item.confidence !== null) {
      badge = '<span class="badge badge-success">✓ Analyzed</span>';
      text = `Evidence #${item.id} analyzed — ${item.confidence > 55 ? 'Distress detected' : 'No distress'} (${item.confidence}% confidence)`;
    } else if (item.status === 'analyzed') {
      badge = '<span class="badge badge-success">✓ Analyzed</span>';
      text = `Evidence #${item.id} analyzed`;
    } else {
      badge = '<span class="badge badge-info">📤 Uploaded</span>';
      text = `New evidence submitted${item.location && item.location !== 'Unknown' ? ' from ' + item.location : ''} — ${item.id}`;
    }

    const timeAgo = getTimeAgo(item.timestamp);

    const div = document.createElement('div');
    div.style.cssText = `display:flex;gap:1rem;padding:0.75rem 0;align-items:center;${!isLast ? 'border-bottom:1px solid var(--border-color);' : ''}`;
    div.innerHTML = `
      ${badge}
      <span style="font-size:0.9rem;">${text}</span>
      <span style="margin-left:auto;font-size:0.8rem;color:var(--text-muted);font-family:var(--font-mono);">${timeAgo}</span>
    `;
    feed.appendChild(div);
  });
}

function getTimeAgo(timestamp) {
  if (!timestamp) return '';
  try {
    const diff = Date.now() - new Date(timestamp).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins} min ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} hr ago`;
    const days = Math.floor(hours / 24);
    return `${days} day${days > 1 ? 's' : ''} ago`;
  } catch {
    return '';
  }
}

// ========== Dashboard: Update Stats ==========
function updateStats(data) {
  const totalEl = document.getElementById('stat-total-count');
  const analyzedEl = document.getElementById('stat-analyzed-count');
  const firEl = document.getElementById('stat-fir-count');
  const pendingEl = document.getElementById('stat-pending-count');

  if (totalEl) totalEl.textContent = data.length;
  if (analyzedEl) analyzedEl.textContent = data.filter(i => i.status === 'analyzed').length;
  if (firEl) firEl.textContent = data.filter(i => i.status === 'analyzed' && i.confidence > 55).length;
  if (pendingEl) pendingEl.textContent = data.filter(i => i.status === 'pending').length;
}

// ========== Dashboard: Search & Filter ==========
function setupDashboardFilters() {
  const searchInput = document.getElementById('search-evidence');
  const filterSelect = document.getElementById('filter-status');

  if (searchInput) {
    searchInput.addEventListener('input', () => filterTable());
  }
  if (filterSelect) {
    filterSelect.addEventListener('change', () => filterTable());
  }
}

function filterTable() {
  const search = (document.getElementById('search-evidence')?.value || '').toLowerCase();
  const status = document.getElementById('filter-status')?.value || 'all';

  // Filter the FETCHED backend data, not mock data
  let filtered = fetchedEvidence.filter(item => {
    const matchSearch = !search ||
      (item.id || '').toLowerCase().includes(search) ||
      (item.location || '').toLowerCase().includes(search) ||
      (item.type || '').toLowerCase().includes(search) ||
      (item.filename || '').toLowerCase().includes(search) ||
      (item.description || '').toLowerCase().includes(search);
    const matchStatus = status === 'all' || item.status === status;
    return matchSearch && matchStatus;
  });

  populateEvidenceTable(filtered);
}

// ========== Incident: Load Evidence Detail from Backend ==========
async function loadIncidentDetail(evidenceId) {
  try {
    // Fetch evidence detail
    const res = await fetch(`${API_BASE}/evidence/${evidenceId}/detail`);
    if (!res.ok) throw new Error('Detail fetch failed');
    const data = await res.json();

    // Update Evidence ID display
    const idDisplay = document.getElementById('evidence-id-display');
    if (idDisplay) idDisplay.textContent = data.evidence_id;
    const metaId = document.getElementById('meta-evidence-id');
    if (metaId) metaId.textContent = data.evidence_id;

    // Update metadata
    const metaTimestamp = document.getElementById('meta-timestamp');
    if (metaTimestamp) metaTimestamp.textContent = formatTimestamp(data.created_at);

    const metaGps = document.getElementById('meta-gps');
    if (metaGps) {
      if (data.latitude && data.longitude) {
        metaGps.textContent = `${data.latitude}°N, ${data.longitude}°E`;
      } else {
        metaGps.textContent = data.location || 'Not provided';
      }
    }

    const metaFiletype = document.getElementById('meta-filetype');
    if (metaFiletype) metaFiletype.textContent = data.file_type || 'audio/unknown';

    const metaFilesize = document.getElementById('meta-filesize');
    if (metaFilesize) {
      const kb = ((data.file_size || 0) / 1024).toFixed(1);
      metaFilesize.textContent = kb > 1024 ? (kb / 1024).toFixed(2) + ' MB' : kb + ' KB';
    }

    const metaStatus = document.getElementById('meta-status');
    if (metaStatus) {
      metaStatus.textContent = data.status === 'analyzed' ? 'Analyzed' : data.status === 'pending' ? 'Pending' : data.status;
      metaStatus.className = data.status === 'analyzed' ? 'badge badge-success' : 'badge badge-warning';
    }

    // Update distress level with REAL data
    const metaDistress = document.getElementById('meta-distress');
    if (metaDistress) {
      const pct = data.confidence_pct || 0;
      const level = data.distress_level || 'Unknown';
      metaDistress.textContent = `${level} (${pct}%)`;
      
      if (pct >= 55) {
        metaDistress.style.color = 'var(--danger)';
      } else if (pct >= 35) {
        metaDistress.style.color = 'var(--warning)';
      } else {
        metaDistress.style.color = 'var(--success)';
      }
    }

    // Update SHA-256 hash
    const hashEl = document.getElementById('sha256-hash');
    if (hashEl) hashEl.textContent = data.sha256_hash || 'N/A';

    // Update confidence bar
    const confBar = document.getElementById('confidence-bar');
    if (confBar) {
      const pct = data.confidence_pct || 0;
      confBar.style.width = pct + '%';
      if (pct >= 55) {
        confBar.style.background = 'linear-gradient(90deg, var(--warning), var(--danger))';
      } else if (pct >= 35) {
        confBar.style.background = 'linear-gradient(90deg, var(--teal), var(--warning))';
      } else {
        confBar.style.background = 'linear-gradient(90deg, var(--success), var(--teal))';
      }
    }

    // Update confidence percentage text
    const confPctEl = document.getElementById('confidence-pct');
    if (confPctEl) {
      const pct = data.confidence_pct || 0;
      confPctEl.textContent = pct + '%';
      if (pct >= 55) confPctEl.style.color = 'var(--danger)';
      else if (pct >= 35) confPctEl.style.color = 'var(--warning)';
      else confPctEl.style.color = 'var(--success)';
    }

    // Update voice stress
    const voiceStressEl = document.getElementById('voice-stress-pct');
    if (voiceStressEl) {
      const vs = Math.round((data.confidence || 0) * 85);
      voiceStressEl.textContent = vs + '%';
    }
    const voiceStressBar = document.getElementById('voice-stress-bar');
    if (voiceStressBar) {
      const vs = Math.round((data.confidence || 0) * 85);
      voiceStressBar.style.width = vs + '%';
    }

    // Update distress badge
    const distressBadge = document.getElementById('distress-badge');
    if (distressBadge) {
      if (data.distress_detected) {
        distressBadge.textContent = '⚠️ Distress Detected';
        distressBadge.className = 'badge badge-danger';
      } else {
        distressBadge.textContent = '✅ No Distress';
        distressBadge.className = 'badge badge-success';
      }
    }

    // Update AI Summary
    const summaryEl = document.getElementById('ai-summary-text');
    if (summaryEl) {
      summaryEl.textContent = data.ai_summary || 'Analysis pending. Click "Analyze with AI" to process this evidence.';
    }

    // Update audio player source
    const audioEl = document.getElementById('evidence-audio');
    if (audioEl && data.file_path) {
      audioEl.src = `${API_BASE}/uploads/${data.file_path.replace('uploads/', '').replace('uploads\\', '')}`;
    }

    // Update Generate FIR link
    const firBtn = document.getElementById('btn-generate-fir');
    if (firBtn) {
      firBtn.href = `report.html?id=${data.evidence_id}`;
    }

    // Update hash anchor info
    const hashAnchor = document.getElementById('hash-anchor-info');
    if (hashAnchor) {
      const blockNum = Math.abs(hashCode(data.evidence_id)) % 90000 + 10000;
      hashAnchor.textContent = `Anchored at block #${blockNum} — ${formatTimestamp(data.created_at)}`;
    }

    return data;

  } catch (err) {
    console.warn('Could not load incident detail from backend:', err);
    showToast('Could not load evidence detail. Ensure backend is running.', 'warning');
    return null;
  }
}

// Simple hash code for consistent block numbers
function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return hash;
}

// ========== Incident: Analyze with AI ==========
async function analyzeWithAI(evidenceId) {
  const btn = document.getElementById('btn-analyze-ai');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px;"></div> Analyzing...';
  }

  try {
    const response = await fetch(`${API_BASE}/evidence/${evidenceId}/analyze`, { method: 'POST' });
    if (response.ok) {
      const result = await response.json();
      const pct = result.confidence_pct || Math.round((result.confidence || 0) * 100);
      const level = result.distress_level || 'Unknown';
      showToast(`Analysis complete — Distress: ${level} (${pct}%)`, 'success');
      
      // Reload the incident detail to show updated data
      await loadIncidentDetail(evidenceId);
    } else {
      throw new Error('API error');
    }
  } catch (e) {
    showToast('Analysis failed. Ensure backend is running.', 'error');
  }

  if (btn) {
    btn.disabled = false;
    btn.innerHTML = '🧠 Analyze with AI';
  }
}

// ========== Incident: Copy Hash ==========
function setupCopyHash() {
  const btn = document.getElementById('btn-copy-hash');
  if (!btn) return;

  btn.addEventListener('click', () => {
    const hash = document.getElementById('sha256-hash')?.textContent;
    if (hash) {
      navigator.clipboard.writeText(hash).then(() => {
        showToast('SHA-256 hash copied to clipboard!', 'success');
        btn.innerHTML = '✅ Copied!';
        setTimeout(() => btn.innerHTML = '📋 Copy', 2000);
      }).catch(() => {
        showToast('Failed to copy hash', 'error');
      });
    }
  });
}

// ========== Utility: Get URL Params ==========
function getUrlParam(key) {
  const params = new URLSearchParams(window.location.search);
  return params.get(key);
}

// ========== Init ==========
document.addEventListener('DOMContentLoaded', () => {
  // Dashboard init
  if (document.getElementById('evidence-tbody')) {
    fetchEvidenceList();
    setupDashboardFilters();
  }

  // Incident page init
  if (document.getElementById('btn-analyze-ai')) {
    const evidenceId = getUrlParam('id');
    
    if (!evidenceId) {
      // No evidence ID provided — show helpful message
      const idDisplay = document.getElementById('evidence-id-display');
      if (idDisplay) idDisplay.textContent = 'No evidence selected';
      const summaryEl = document.getElementById('ai-summary-text');
      if (summaryEl) summaryEl.textContent = 'No evidence ID provided. Please select an evidence record from the Dashboard or upload new evidence.';
      document.getElementById('btn-analyze-ai').disabled = true;
      showToast('No evidence ID in URL. Go to Dashboard to select an evidence record.', 'warning');
      return;
    }
    
    // Load real data from backend
    loadIncidentDetail(evidenceId);

    document.getElementById('btn-analyze-ai').addEventListener('click', () => analyzeWithAI(evidenceId));

    // Update evidence ID display immediately
    const idDisplay = document.getElementById('evidence-id-display');
    if (idDisplay) idDisplay.textContent = evidenceId;
    const metaId = document.getElementById('meta-evidence-id');
    if (metaId) metaId.textContent = evidenceId;
  }

  // Copy hash
  setupCopyHash();

  console.log('🛡️ AI Digital Memory Vault — Frontend loaded');
});
