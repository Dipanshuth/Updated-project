const API_BASE = window.API_BASE || (window.getApiBaseUrl ? window.getApiBaseUrl() : `http://${window.location.hostname || 'localhost'}:8000`);

function updateStep(stepId, state) {
  const el = document.getElementById(stepId);
  if (!el) return;
  
  el.className = 'pipeline-step';
  const icon = el.querySelector('.step-icon');
  
  if (state === 'active') {
    el.classList.add('active');
    icon.innerHTML = '<div class="pulse" style="width:10px;height:10px;background:var(--teal);border-radius:50%;"></div>';
  } else if (state === 'completed') {
    el.classList.add('completed');
    icon.innerHTML = '✓';
  } else if (state === 'error') {
    el.classList.add('active');
    el.style.color = 'var(--danger)';
    icon.innerHTML = '✕';
  }
}

function updateVisual(state, text, subtitle) {
  const visual = document.getElementById('status-visual');
  const titleEl = document.getElementById('status-title');
  const subEl = document.getElementById('status-subtitle');
  
  titleEl.innerText = text;
  subEl.innerText = subtitle;
  
  visual.className = 'status-circle';
  if (state === 'recording') {
    visual.classList.add('recording', 'pulsing');
    visual.innerHTML = '🎙️';
  } else if (state === 'processing') {
    visual.classList.add('processing', 'pulsing');
    visual.innerHTML = '🧠';
  } else if (state === 'success') {
    visual.style.borderColor = 'var(--success)';
    visual.style.background = 'rgba(0, 201, 177, 0.2)';
    visual.innerHTML = '✅';
  } else if (state === 'low') {
    visual.style.borderColor = 'var(--success)';
    visual.style.background = 'rgba(0, 201, 177, 0.2)';
    visual.innerHTML = '✅';
  } else if (state === 'medium') {
    visual.style.borderColor = 'var(--warning)';
    visual.style.background = 'rgba(255, 165, 2, 0.2)';
    visual.innerHTML = '⚠️';
  } else if (state === 'high') {
    visual.style.borderColor = 'var(--danger)';
    visual.style.background = 'rgba(255, 71, 87, 0.2)';
    visual.innerHTML = '🚨';
  }
}

function showResults(data) {
  const panel = document.getElementById('results-panel');
  if (!panel) return;

  const confidence = data.confidence || 0;
  const confidencePct = Math.round(confidence * 100);
  const level = data.distress_level || 'Unknown';
  const detected = data.distress_detected;
  const message = data.message || data.ai_summary || '';
  const evidenceId = data.evidence_id || '—';

  // Determine color class
  let colorClass = 'low';
  if (confidencePct >= 55) colorClass = 'high';
  else if (confidencePct >= 35) colorClass = 'medium';

  // Populate results
  document.getElementById('result-evidence-id').textContent = evidenceId;
  
  const levelEl = document.getElementById('result-distress-level');
  levelEl.textContent = level;
  levelEl.className = 'result-value ' + colorClass;

  const confEl = document.getElementById('result-confidence');
  confEl.textContent = confidencePct + '%';
  confEl.className = 'result-value ' + colorClass;

  // Animate confidence bar
  const bar = document.getElementById('result-confidence-bar');
  let barColor = 'linear-gradient(90deg, var(--success), var(--teal))';
  if (confidencePct >= 55) barColor = 'linear-gradient(90deg, var(--warning), var(--danger))';
  else if (confidencePct >= 35) barColor = 'linear-gradient(90deg, var(--teal), var(--warning))';
  bar.style.background = barColor;
  setTimeout(() => { bar.style.width = confidencePct + '%'; }, 100);

  const detectedEl = document.getElementById('result-detected');
  detectedEl.textContent = detected ? '⚠️ YES' : '✅ NO';
  detectedEl.className = 'result-value ' + (detected ? 'high' : 'low');

  document.getElementById('result-status').textContent = '✓ Complete';

  const msgEl = document.getElementById('result-message');
  msgEl.textContent = message;
  msgEl.className = 'result-message ' + colorClass;

  // Update action links
  document.getElementById('btn-view-report').href = `report.html?id=${evidenceId}`;
  document.getElementById('btn-view-incident').href = `incident.html?id=${evidenceId}`;

  // Show the panel
  panel.style.display = 'block';
}

function resetDemo() {
  // Hide results
  document.getElementById('results-panel').style.display = 'none';
  document.getElementById('pipeline-ui').style.display = 'none';

  // Reset visual
  const visual = document.getElementById('status-visual');
  visual.className = 'status-circle pulsing';
  visual.style.borderColor = '';
  visual.style.background = '';
  visual.innerHTML = '🛡️';

  document.getElementById('status-title').innerText = 'Protection Active';
  document.getElementById('status-subtitle').innerText = 'The system is monitoring for distress signals via microphone and sensors.';

  // Reset pipeline steps
  ['step-detect', 'step-record', 'step-upload', 'step-analyze', 'step-infer', 'step-report'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.className = 'pipeline-step';
      el.style.color = '';
      const icon = el.querySelector('.step-icon');
      const num = id.replace('step-', '');
      const nums = { detect: '1', record: '2', upload: '3', analyze: '4', infer: '5', report: '6' };
      if (icon) icon.innerHTML = nums[num] || '';
    }
  });

  // Re-enable button
  const btn = document.getElementById('btn-trigger-demo');
  btn.disabled = false;
  btn.innerText = '🚨 Simulate Trigger';

  // Show demo controls
  document.getElementById('demo-controls').style.display = '';
}

async function startDemoPipeline() {
  document.getElementById('btn-trigger-demo').disabled = true;
  document.getElementById('pipeline-ui').style.display = 'block';
  document.getElementById('results-panel').style.display = 'none';

  // State: Triggered
  updateVisual('processing', 'Initiating Pipeline...', 'Checking backend connection...');
  updateStep('step-detect', 'active');
  
  let evidenceId = null;
  let analysisResult = null;

  try {
    // Pre-flight: Check backend is reachable
    try {
      const healthCheck = await fetch(`${API_BASE}/health`, {
        signal: AbortSignal.timeout(3000)
      });
      if (!healthCheck.ok) throw new Error('Backend not healthy');
    } catch (connErr) {
      updateVisual('processing', 'Backend Not Running', 'Start the backend: cd backend && py -m uvicorn main:app --port 8000');
      document.getElementById('btn-trigger-demo').innerText = '⚠️ Start Backend First';
      document.getElementById('btn-trigger-demo').disabled = false;
      return;
    }

    updateVisual('processing', 'Initiating Pipeline...', 'Preparing distress detection system');

    // 1. Detect Trigger (initial acknowledgement)
    const detectRes = await fetch(`${API_BASE}/detect-trigger`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trigger_type: 'simulated' })
    }).then(r => r.json());

    updateStep('step-detect', 'completed');
    
    // 2. Recording (Real Microphone Audio)
    updateVisual('recording', 'Recording Audio...', 'Speak into your microphone. Recording for 6 seconds...');
    updateStep('step-record', 'active');
    
    let audioBlob = null;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks = [];
      
      mediaRecorder.addEventListener("dataavailable", event => {
        audioChunks.push(event.data);
      });
      
      const recordPromise = new Promise(resolve => {
        mediaRecorder.addEventListener("stop", () => {
          audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          resolve();
        });
      });
      
      mediaRecorder.start();
      await new Promise(r => setTimeout(r, 6000)); // Record for 6 seconds
      mediaRecorder.stop();
      await recordPromise;
      
      // Stop all tracks to release microphone
      stream.getTracks().forEach(track => track.stop());
    } catch(err) {
      console.warn("Microphone access denied or unavailable, falling back to dummy audio.", err);
      audioBlob = new Blob(["dummy audio content for fallback"], { type: 'audio/webm' });
      await new Promise(r => setTimeout(r, 3000));
    }
    
    updateStep('step-record', 'completed');

    // 3. Upload Evidence
    updateStep('step-upload', 'active');
    updateVisual('processing', 'Uploading Evidence...', 'Securing file with SHA-256 hash');

    const formData = new FormData();
    formData.append('file', audioBlob, 'evidence_recording.webm');
    formData.append('gps_data', '28.6139, 77.2090');
    formData.append('device_id', 'LIVE_DEVICE_01');
    formData.append('timestamp', new Date().toISOString());

    const uploadRes = await fetch(`${API_BASE}/upload-evidence`, {
      method: 'POST',
      body: formData
    }).then(r => r.json());
    
    evidenceId = uploadRes.evidence_id;
    updateStep('step-upload', 'completed');

    // 4. Audio Analysis — send recorded audio to analysis endpoint
    updateStep('step-analyze', 'active');
    updateVisual('processing', 'Analyzing Audio...', 'Running distress detection on your voice recording');

    const analyzeFormData = new FormData();
    analyzeFormData.append('file', audioBlob, 'evidence_recording.webm');

    analysisResult = await fetch(`${API_BASE}/detect-trigger-audio`, {
      method: 'POST',
      body: analyzeFormData
    }).then(r => r.json());

    updateStep('step-analyze', 'completed');

    // 5. Inference & Timeline
    updateStep('step-infer', 'active');
    updateVisual('processing', 'AI Inference...', 'Extracting timeline and generating analysis');
    
    const inferRes = await fetch(`${API_BASE}/run-inference`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ evidence_id: evidenceId })
    }).then(r => r.json());
    
    // Generate Timeline
    await fetch(`${API_BASE}/generate-timeline?evidence_id=${evidenceId}`);
    
    updateStep('step-infer', 'completed');

    // 6. Report
    updateStep('step-report', 'active');
    updateVisual('processing', 'Generating FIR...', 'Formatting legal report');
    
    await fetch(`${API_BASE}/generate-report?evidence_id=${evidenceId}`);
    
    updateStep('step-report', 'completed');

    // Determine final visual state based on distress level
    const confidence = analysisResult.confidence || inferRes.confidence || 0;
    const confidencePct = Math.round(confidence * 100);
    const level = analysisResult.distress_level || inferRes.distress_level || 'Low';

    let visualState = 'low';
    if (confidencePct >= 55) visualState = 'high';
    else if (confidencePct >= 35) visualState = 'medium';

    updateVisual(visualState, 'Pipeline Complete', `Distress: ${level} (${confidencePct}%) — Evidence ID: ${evidenceId}`);
    
    // Show persistent results panel — NO auto-redirect
    showResults({
      evidence_id: evidenceId,
      confidence: confidence,
      distress_level: level,
      distress_detected: analysisResult.distress_detected || false,
      message: inferRes.ai_summary || analysisResult.message || 'Analysis complete.',
      ai_summary: inferRes.ai_summary || ''
    });

    // Hide demo controls since results are shown
    document.getElementById('demo-controls').style.display = 'none';

  } catch (err) {
    console.error(err);
    updateVisual('processing', 'System Error', 'Ensure backend is running on localhost:8000');
    document.getElementById('btn-trigger-demo').innerText = 'Backend Error. Retry?';
    document.getElementById('btn-trigger-demo').disabled = false;
  }
}
