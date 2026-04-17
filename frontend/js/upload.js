/**
 * AI Digital Memory Vault — Upload & Recording Logic
 * Features: MediaRecorder API, Waveform Visualization, File Upload, GPS Capture
 */

const API_BASE = 'http://localhost:8000';

// ========== State ==========
let mediaRecorder = null;
let audioChunks = [];
let audioBlob = null;
let audioStream = null;
let audioContext = null;
let analyser = null;
let animationId = null;
let recordingStartTime = null;
let timerInterval = null;

// ========== Toast (duplicate-safe) ==========
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
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ========== Audio Recording ==========
async function startRecording() {
  try {
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });

    // Setup MediaRecorder
    mediaRecorder = new MediaRecorder(audioStream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
      audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      const audioUrl = URL.createObjectURL(audioBlob);

      const audioEl = document.getElementById('recorded-audio');
      audioEl.src = audioUrl;
      document.getElementById('recorded-audio-container').classList.remove('hidden');
      document.getElementById('btn-play-recording').disabled = false;
      document.getElementById('btn-clear-recording').disabled = false;

      showToast('Recording saved successfully!', 'success');
    };

    mediaRecorder.start();
    recordingStartTime = Date.now();
    startTimer();
    startWaveform();

    // Update UI
    const micBtn = document.getElementById('mic-button');
    micBtn.classList.add('recording');
    micBtn.innerHTML = '⏹️';
    document.getElementById('recording-label').textContent = 'Recording... Tap to stop';

    showToast('Recording started', 'info');
  } catch (err) {
    showToast('Microphone access denied. Please allow microphone permissions.', 'error');
    console.error('Microphone error:', err);
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
  }

  // Stop stream tracks
  if (audioStream) {
    audioStream.getTracks().forEach(track => track.stop());
    audioStream = null;
  }

  stopTimer();
  stopWaveform();

  // Update UI
  const micBtn = document.getElementById('mic-button');
  micBtn.classList.remove('recording');
  micBtn.innerHTML = '🎙️';
  document.getElementById('recording-label').textContent = 'Recording complete';
}

function toggleRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    stopRecording();
  } else {
    startRecording();
  }
}

// ========== Recording Timer ==========
function startTimer() {
  const timerEl = document.getElementById('recording-timer');
  timerInterval = setInterval(() => {
    const elapsed = Date.now() - recordingStartTime;
    const mins = Math.floor(elapsed / 60000).toString().padStart(2, '0');
    const secs = Math.floor((elapsed % 60000) / 1000).toString().padStart(2, '0');
    timerEl.textContent = `${mins}:${secs}`;
  }, 100);
}

function stopTimer() {
  clearInterval(timerInterval);
}

// ========== Waveform Visualization ==========
function startWaveform() {
  const canvas = document.getElementById('waveform-canvas');
  const ctx = canvas.getContext('2d');

  // Set canvas size
  canvas.width = canvas.parentElement.offsetWidth;
  canvas.height = canvas.parentElement.offsetHeight;

  audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const source = audioContext.createMediaStreamSource(audioStream);
  analyser = audioContext.createAnalyser();
  analyser.fftSize = 256;

  source.connect(analyser);

  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  function draw() {
    animationId = requestAnimationFrame(draw);

    analyser.getByteFrequencyData(dataArray);

    ctx.fillStyle = '#0d1319';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const barWidth = (canvas.width / bufferLength) * 2;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const barHeight = (dataArray[i] / 255) * canvas.height * 0.85;

      // Gradient from teal to cyan
      const gradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
      gradient.addColorStop(0, '#00C9B1');
      gradient.addColorStop(1, '#006655');

      ctx.fillStyle = gradient;
      ctx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);

      x += barWidth + 1;
    }
  }

  draw();
}

function stopWaveform() {
  cancelAnimationFrame(animationId);
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }

  // Draw flat line
  const canvas = document.getElementById('waveform-canvas');
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#0d1319';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#00C9B1';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, canvas.height / 2);
  ctx.lineTo(canvas.width, canvas.height / 2);
  ctx.stroke();
}

// ========== File Upload ==========
function setupFileUpload() {
  const dropzone = document.getElementById('upload-dropzone');
  const fileInput = document.getElementById('file-input');

  if (!dropzone || !fileInput) return;

  // Click to browse
  dropzone.addEventListener('click', () => fileInput.click());

  // Drag & drop events
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
  });

  // File input change
  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFile(e.target.files[0]);
  });

  // Remove file
  document.getElementById('btn-remove-file')?.addEventListener('click', () => {
    fileInput.value = '';
    document.getElementById('file-preview').classList.add('hidden');
    dropzone.style.display = '';
    showToast('File removed', 'info');
  });
}

function handleFile(file) {
  // Validate type
  if (!file.type.startsWith('audio/')) {
    showToast('Please upload an audio file (MP3, WAV, OGG, WEBM)', 'error');
    return;
  }

  // Validate size (50MB max)
  if (file.size > 50 * 1024 * 1024) {
    showToast('File too large. Maximum size is 50MB.', 'error');
    return;
  }

  document.getElementById('file-name').textContent = file.name;
  document.getElementById('file-size').textContent = formatFileSize(file.size);
  document.getElementById('file-preview').classList.remove('hidden');
  document.getElementById('upload-dropzone').style.display = 'none';

  showToast(`File "${file.name}" selected`, 'success');
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ========== GPS Location ==========
function setupGPS() {
  const btn = document.getElementById('btn-get-location');
  if (!btn) return;

  btn.addEventListener('click', () => {
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:14px;height:14px;border-width:2px;"></div> Locating...';

    if (!navigator.geolocation) {
      showToast('Geolocation not supported by your browser', 'error');
      btn.disabled = false;
      btn.innerHTML = '📍 Get My Location';
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude.toFixed(6);
        const lng = position.coords.longitude.toFixed(6);

        // Update UI
        document.getElementById('gps-lat').value = lat;
        document.getElementById('gps-lng').value = lng;
        document.getElementById('gps-lat-lng').textContent = `Lat: ${lat}, Lng: ${lng}`;
        document.getElementById('gps-result').classList.remove('hidden');
        document.getElementById('gps-badge').textContent = '✓ Captured';
        document.getElementById('gps-badge').className = 'badge badge-success';

        // Show map
        const mapIframe = document.getElementById('map-iframe');
        mapIframe.src = `https://www.openstreetmap.org/export/embed.html?bbox=${lng - 0.01},${lat - 0.01},${parseFloat(lng) + 0.01},${parseFloat(lat) + 0.01}&layer=mapnik&marker=${lat},${lng}`;

        btn.innerHTML = '✅ Location Captured';
        showToast(`GPS Location: ${lat}, ${lng}`, 'success');
      },
      (error) => {
        const messages = {
          1: 'Location access denied. Please allow location permissions.',
          2: 'Position unavailable. Try again.',
          3: 'Location request timed out. Try again.',
        };
        showToast(messages[error.code] || 'Failed to get location', 'error');
        btn.disabled = false;
        btn.innerHTML = '📍 Get My Location';
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  });
}

// ========== Form Submission ==========
function setupFormSubmission() {
  const form = document.getElementById('evidence-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = document.getElementById('btn-submit-evidence');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px;"></div> Uploading...';

    const formData = new FormData();

    // Add recorded audio or uploaded file
    const fileInput = document.getElementById('file-input');
    if (audioBlob) {
      formData.append('file', audioBlob, 'recording.webm');
    } else if (fileInput.files.length > 0) {
      formData.append('file', fileInput.files[0]);
    } else {
      showToast('Please record audio or upload a file', 'warning');
      submitBtn.disabled = false;
      submitBtn.innerHTML = '🚀 Submit Evidence';
      return;
    }

    // Add metadata
    formData.append('description', document.getElementById('incident-description')?.value || '');
    formData.append('datetime', document.getElementById('incident-datetime')?.value || '');
    formData.append('location', document.getElementById('incident-location')?.value || '');
    formData.append('latitude', document.getElementById('gps-lat')?.value || '');
    formData.append('longitude', document.getElementById('gps-lng')?.value || '');

    try {
      const response = await fetch(`${API_BASE}/evidence/upload`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        showToast(`Evidence uploaded successfully! ID: ${result.evidence_id}`, 'success');

        // Auto-trigger AI analysis so it appears analyzed in dashboard
        try {
          showToast('Running AI analysis...', 'info');
          await fetch(`${API_BASE}/evidence/${result.evidence_id}/analyze`, { method: 'POST' });
          showToast('AI analysis complete!', 'success');
        } catch (analyzeErr) {
          console.warn('Auto-analysis failed, evidence saved as pending:', analyzeErr);
        }

        // Redirect to incident detail
        setTimeout(() => {
          window.location.href = `incident.html?id=${result.evidence_id}`;
        }, 1500);
        return;
      }
      throw new Error('Upload failed');
    } catch (err) {
      console.error('Upload error:', err);
      showToast('Upload failed. Please ensure the backend server is running on localhost:8000.', 'error');
    }

    submitBtn.disabled = false;
    submitBtn.innerHTML = '🚀 Submit Evidence';
  });
}

// ========== Reset Form ==========
function setupReset() {
  const btn = document.getElementById('btn-reset-form');
  if (!btn) return;

  btn.addEventListener('click', () => {
    // Stop recording if active
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      stopRecording();
    }

    // Reset audio
    audioBlob = null;
    audioChunks = [];
    document.getElementById('recorded-audio-container').classList.add('hidden');
    document.getElementById('btn-play-recording').disabled = true;
    document.getElementById('btn-clear-recording').disabled = true;
    document.getElementById('recording-timer').textContent = '00:00';
    document.getElementById('recording-label').textContent = 'Tap to start recording';

    // Reset file
    document.getElementById('file-input').value = '';
    document.getElementById('file-preview').classList.add('hidden');
    document.getElementById('upload-dropzone').style.display = '';

    // Reset GPS
    document.getElementById('gps-result').classList.add('hidden');
    document.getElementById('gps-badge').textContent = 'Awaiting...';
    document.getElementById('gps-badge').className = 'badge badge-success';
    document.getElementById('btn-get-location').disabled = false;
    document.getElementById('btn-get-location').innerHTML = '📍 Get My Location';

    // Reset form fields
    document.getElementById('evidence-form').reset();

    // Reset waveform
    const canvas = document.getElementById('waveform-canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.parentElement.offsetWidth;
    canvas.height = canvas.parentElement.offsetHeight;
    ctx.fillStyle = '#0d1319';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    showToast('Form reset', 'info');
  });
}

// ========== Init ==========
document.addEventListener('DOMContentLoaded', () => {
  // Mic button
  const micBtn = document.getElementById('mic-button');
  if (micBtn) {
    micBtn.addEventListener('click', toggleRecording);
  }

  // Play recording
  document.getElementById('btn-play-recording')?.addEventListener('click', () => {
    const audioEl = document.getElementById('recorded-audio');
    if (audioEl) audioEl.play();
  });

  // Clear recording
  document.getElementById('btn-clear-recording')?.addEventListener('click', () => {
    audioBlob = null;
    audioChunks = [];
    document.getElementById('recorded-audio-container').classList.add('hidden');
    document.getElementById('btn-play-recording').disabled = true;
    document.getElementById('btn-clear-recording').disabled = true;
    document.getElementById('recording-timer').textContent = '00:00';
    document.getElementById('recording-label').textContent = 'Tap to start recording';

    const canvas = document.getElementById('waveform-canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.parentElement.offsetWidth;
    canvas.height = canvas.parentElement.offsetHeight;
    ctx.fillStyle = '#0d1319';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    showToast('Recording cleared', 'info');
  });

  // Set default datetime
  const dtInput = document.getElementById('incident-datetime');
  if (dtInput) {
    const now = new Date();
    dtInput.value = now.toISOString().slice(0, 16);
  }

  // Setup features
  setupFileUpload();
  setupGPS();
  setupFormSubmission();
  setupReset();

  // Init waveform canvas
  const canvas = document.getElementById('waveform-canvas');
  if (canvas) {
    canvas.width = canvas.parentElement.offsetWidth;
    canvas.height = canvas.parentElement.offsetHeight;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#0d1319';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#1e2a38';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, canvas.height / 2);
    ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();
  }

  console.log('🎙️ Upload module loaded');
});
