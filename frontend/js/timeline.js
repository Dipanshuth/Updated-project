/**
 * AI Digital Memory Vault — Timeline Rendering
 * Renders and animates the vertical timeline on the incident detail page
 */

// ========== Mock Timeline Data ==========
const MOCK_TIMELINE = [
  {
    time: '14:32:00',
    title: '📤 Evidence Received',
    description: 'Audio file uploaded and queued for processing',
    active: true,
  },
  {
    time: '14:32:05',
    title: '🔐 Hash Generated',
    description: 'SHA-256 hash computed and blockchain anchor initiated',
    active: true,
  },
  {
    time: '14:32:12',
    title: '🧠 AI Analysis Started',
    description: 'Processing audio with distress detection model',
    active: true,
  },
  {
    time: '14:33:01',
    title: '⚠️ Distress Detected',
    description: 'Confidence: 87% — Elevated vocal stress patterns identified at 01:42 mark',
    active: true,
  },
  {
    time: '14:33:15',
    title: '📝 Transcript Generated',
    description: 'Full audio transcription completed (324 words)',
    active: true,
  },
  {
    time: '14:34:02',
    title: '📅 Timeline Generated',
    description: 'Incident sequence reconstructed with 6 key events',
    active: false,
  },
];

// ========== Render Timeline ==========
function renderTimeline(container, events) {
  if (!container) return;

  container.innerHTML = '';

  events.forEach((event, index) => {
    const item = document.createElement('div');
    item.className = `timeline-item ${event.active ? 'active' : ''}`;
    item.style.opacity = '0';
    item.style.transform = 'translateX(-20px)';

    item.innerHTML = `
      <div class="timeline-time">${event.time}</div>
      <div class="timeline-content">
        <h4>${event.title}</h4>
        <p>${event.description}</p>
      </div>
    `;

    container.appendChild(item);

    // Animate in with stagger
    setTimeout(() => {
      item.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
      item.style.opacity = '1';
      item.style.transform = 'translateX(0)';
    }, 100 + index * 150);
  });
}

// ========== Fetch Timeline from Backend ==========
async function fetchTimeline(evidenceId) {
  const API_BASE = window.API_BASE || (window.getApiBaseUrl ? window.getApiBaseUrl() : `http://${window.location.hostname || 'localhost'}:8000`);

  try {
    const response = await fetch(`${API_BASE}/evidence/${evidenceId}/timeline`);
    if (response.ok) {
      const data = await response.json();
      return data.timeline || data;
    }
  } catch (e) {
    console.log('Using mock timeline data');
  }

  return MOCK_TIMELINE;
}

// ========== Init ==========
document.addEventListener('DOMContentLoaded', async () => {
  const timelineContainer = document.getElementById('incident-timeline');
  if (!timelineContainer) return;

  // Get evidence ID from URL
  const params = new URLSearchParams(window.location.search);
  const evidenceId = params.get('id');

  if (!evidenceId) {
    timelineContainer.innerHTML = '<div style="text-align:center; color:var(--text-muted); padding:2rem;">No evidence selected. Please choose an evidence record from the Dashboard.</div>';
    return;
  }

  // Fetch and render timeline
  const events = await fetchTimeline(evidenceId);
  renderTimeline(timelineContainer, events);

  console.log('📅 Timeline module loaded');
});
