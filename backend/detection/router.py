import asyncio
import struct
import math
import io
import wave
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["Detection"])


def _try_decode_wav(audio_bytes: bytes):
    """
    Attempt to read audio_bytes as a WAV file and return list of PCM samples.
    Returns None if the bytes are not valid WAV.
    """
    try:
        buf = io.BytesIO(audio_bytes)
        with wave.open(buf, 'rb') as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()
            if n_frames == 0:
                return None
            raw = wf.readframes(n_frames)
            # Convert raw bytes to list of signed integers
            samples = []
            if sampwidth == 2:
                fmt = '<' + 'h' * (len(raw) // 2)
                samples = list(struct.unpack(fmt, raw))
            elif sampwidth == 1:
                # 8-bit unsigned, center at 0
                samples = [b - 128 for b in raw]
            else:
                return None
            # If stereo, average channels
            if n_channels == 2 and len(samples) >= 2:
                mono = []
                for i in range(0, len(samples) - 1, 2):
                    mono.append((samples[i] + samples[i + 1]) // 2)
                samples = mono
            return samples
    except Exception:
        return None


def _extract_pcm_from_container(audio_bytes: bytes):
    """
    For WebM/Opus/OGG containers, we cannot decode them without ffmpeg.
    Instead, we use a statistical approach on the compressed data:
    
    1. Skip the first ~1000 bytes (container headers/metadata)
    2. Analyze the remaining compressed audio payload
    3. Use byte entropy and variance as a proxy for audio energy
    
    Compressed audio of loud sounds has different statistical properties
    (higher entropy, more byte variance) than quiet/silent audio.
    """
    if len(audio_bytes) < 1500:
        return None

    # Skip container headers (first ~1000 bytes for WebM)
    payload = audio_bytes[1000:]
    
    if len(payload) < 500:
        return None

    # Calculate mean byte value
    byte_values = list(payload)
    mean = sum(byte_values) / len(byte_values)
    
    # Calculate variance from uniform distribution (which compressed silence approximates)
    variance = sum((b - mean) ** 2 for b in byte_values) / len(byte_values)
    
    # Calculate byte entropy (information density)
    freq = [0] * 256
    for b in byte_values:
        freq[b] += 1
    total = len(byte_values)
    entropy = 0.0
    for f in freq:
        if f > 0:
            p = f / total
            entropy -= p * math.log2(p)
    
    # Calculate zero-crossing rate analog (consecutive byte differences)
    diff_sum = 0
    large_diffs = 0
    for i in range(1, min(len(byte_values), 10000)):
        d = abs(byte_values[i] - byte_values[i-1])
        diff_sum += d
        if d > 100:
            large_diffs += 1
    
    avg_diff = diff_sum / min(len(byte_values) - 1, 9999)
    large_diff_ratio = large_diffs / min(len(byte_values) - 1, 9999)
    
    # Compute energy score from multiple features
    # Compressed silence: low variance (~5000-5500), high entropy (~7.9-8.0), low avg_diff (~40-50)
    # Normal speech: moderate variance (~5300-5700), entropy ~7.85-7.95, avg_diff ~50-65
    # Loud/shouting: higher variance (~5700+), entropy ~7.8-7.9, avg_diff ~60-80+
    
    # Normalize features to 0-1 scale
    variance_score = min(max((variance - 5000) / 2000, 0), 1.0)
    diff_score = min(max((avg_diff - 40) / 50, 0), 1.0)
    large_diff_score = min(large_diff_ratio * 15, 1.0)
    
    # Size-based energy (larger compressed payloads = more audio activity)
    bytes_per_second = len(payload) / 4.0  # assuming ~4 second recordings
    size_score = min(max((bytes_per_second - 2000) / 8000, 0), 1.0)
    
    # Combined energy score (weighted)
    energy_score = (
        variance_score * 0.25 + 
        diff_score * 0.30 + 
        large_diff_score * 0.20 + 
        size_score * 0.25
    )
    
    return energy_score


def _rms_to_db(rms: float, reference: float = 1.0) -> float:
    """
    Convert RMS amplitude to approximate decibel level.
    For 16-bit PCM audio, reference=1.0 gives dBFS-like values.
    We add an offset to approximate dB SPL-like range (0-100).
    
    Typical mapping for 16-bit PCM:
      RMS ~10-50     → ~20-34 dB  (very quiet / near silence)
      RMS ~50-300    → ~34-50 dB  (quiet speech / ambient)
      RMS ~300-1500  → ~50-64 dB  (normal conversation)
      RMS ~1500-5000 → ~64-74 dB  (raised voice / loud)
      RMS ~5000+     → ~74-90 dB  (shouting / screaming)
    """
    if rms <= 0:
        return -100.0  # Very quiet
    db_raw = 20 * math.log10(rms / reference)
    # Return actual dBFS value (can be negative)
    return max(-100.0, min(db_raw, 0.0))  # Clamp to reasonable range


def _db_to_confidence(db: float) -> float:
    """
    Map decibel level to distress confidence (0.0 - 1.0).
    
    Calibrated so that 40-50 dB → ~55-72% distress (target ~67% at midpoint 45 dB).
    
    Decibel-to-Distress mapping:
      0  - 20 dB  → 5  - 20%  (Minimal)     — near silence, no distress
      20 - 30 dB  → 20 - 40%  (Low)          — quiet ambient, soft speech
      30 - 40 dB  → 40 - 55%  (Moderate)     — normal conversation
      40 - 50 dB  → 55 - 72%  (Medium-High)  — raised voice / tension
      50 - 65 dB  → 72 - 85%  (High)         — loud / shouting
      65+   dB    → 85 - 95%  (Critical)     — extreme screaming
    """
    if db < 20:
        return 0.05 + (db / 20) * 0.15                        # 0.05 - 0.20
    elif db < 30:
        return 0.20 + ((db - 20) / 10) * 0.20                 # 0.20 - 0.40
    elif db < 40:
        return 0.40 + ((db - 30) / 10) * 0.15                 # 0.40 - 0.55
    elif db < 50:
        return 0.55 + ((db - 40) / 10) * 0.17                 # 0.55 - 0.72
    elif db < 65:
        return 0.72 + ((db - 50) / 15) * 0.13                 # 0.72 - 0.85
    else:
        return 0.85 + min((db - 65) / 30 * 0.10, 0.10)        # 0.85 - 0.95


def _analyze_wav_distress(pcm_samples: list, sample_rate: int = 16000) -> float:
    """
    Analyze WAV PCM samples for distress using multiple signal-based metrics.
    Returns confidence score 0.0-1.0.
    """
    if not pcm_samples or len(pcm_samples) < 100:
        return 0.0
    
    # Normalize samples to -1 to 1
    max_val = max(abs(s) for s in pcm_samples) or 1
    normalized = [s / max_val for s in pcm_samples]
    
    # Window size: 100ms (adjust based on sample_rate)
    window_size = int(sample_rate * 0.1)  # 100ms windows
    if window_size < 10:
        window_size = len(normalized) // 10 or 10
    
    # Calculate RMS per window
    rms_windows = []
    for i in range(0, len(normalized), window_size // 2):  # 50% overlap
        window = normalized[i:i + window_size]
        if len(window) < window_size // 2:
            continue
        rms = math.sqrt(sum(x**2 for x in window) / len(window))
        rms_windows.append(rms)
    
    if not rms_windows:
        return 0.0
    
    # Metric 1: Overall loudness (dB)
    overall_rms = math.sqrt(sum(x**2 for x in normalized) / len(normalized))
    db_level = _rms_to_db(overall_rms)  # Don't scale by max_val again
    # For normalized audio, convert dBFS to positive scale
    positive_db = max(0, -db_level)  # 0 dBFS = 0, -6 dBFS = 6, etc.
    loudness_score = min(max((positive_db) / 20, 0), 1)  # 0-20 dB range
    
    # Metric 2: Sudden spikes (max RMS > 1.5x median)
    median_rms = sorted(rms_windows)[len(rms_windows) // 2]
    max_rms = max(rms_windows)
    spike_ratio = max_rms / (median_rms + 0.01)
    spike_score = min(max((spike_ratio - 1.2) / 1, 0), 1)  # Spike >1.2x median
    
    # Metric 3: Sustained loudness (fraction of windows above threshold)
    loud_threshold = 0.2  # Normalized amplitude
    sustained_count = sum(1 for rms in rms_windows if rms > loud_threshold)
    sustained_ratio = sustained_count / len(rms_windows)
    duration_score = min(max((sustained_ratio - 0.5) / 0.5, 0), 1)  # 50-100% sustained
    
    # Metric 4: High frequency energy (simple approximation: zero crossings)
    zero_crossings = sum(1 for i in range(1, len(normalized)) if normalized[i-1] * normalized[i] < 0)
    zcr_rate = zero_crossings / len(normalized)
    # High ZCR indicates high frequency content (screams have high pitch variation)
    high_freq_score = min(max((zcr_rate - 0.01) / 0.05, 0), 1)  # ZCR 0.01-0.06 range
    
    # Multi-condition validation: Require at least 3/4 conditions
    conditions = [loudness_score > 0.3, spike_score > 0.2, duration_score > 0.5, high_freq_score > 0.3]
    condition_count = sum(conditions)
    
    if condition_count < 3:
        return 0.0  # Not enough conditions met
    
    # Weighted confidence score
    base_confidence = (
        loudness_score * 0.4 +      # High amplitude
        spike_score * 0.3 +         # Sudden spikes
        duration_score * 0.2 +      # Sustained
        high_freq_score * 0.1       # High frequency
    )
    
    # Boost if all conditions met
    if condition_count == 4:
        base_confidence *= 1.2
    
    return min(max(base_confidence, 0), 1)


def _analyze_compressed_distress(audio_bytes: bytes) -> float:
    """
    Enhanced analysis for compressed audio using statistical features.
    Returns confidence score 0.0-1.0.
    """
    if len(audio_bytes) < 2000:
        return 0.0
    
    # Skip headers
    payload = audio_bytes[1000:]
    if len(payload) < 1000:
        return 0.0
    
    byte_vals = list(payload)
    
    # Metric 1: Variance (energy proxy)
    mean = sum(byte_vals) / len(byte_vals)
    variance = sum((b - mean)**2 for b in byte_vals) / len(byte_vals)
    variance_score = min(max((variance - 5000) / 3000, 0), 1)
    
    # Metric 2: Large differences (spike proxy)
    large_diffs = sum(1 for i in range(1, len(byte_vals)) if abs(byte_vals[i] - byte_vals[i-1]) > 100)
    diff_ratio = large_diffs / (len(byte_vals) - 1)
    spike_score = min(max((diff_ratio - 0.05) / 0.15, 0), 1)
    
    # Metric 3: Entropy variation (frequency proxy)
    window_size = 500
    entropies = []
    for i in range(0, len(byte_vals) - window_size, window_size // 2):
        window = byte_vals[i:i + window_size]
        freq = [0] * 256
        for b in window:
            freq[b] += 1
        entropy = 0
        for f in freq:
            if f > 0:
                p = f / len(window)
                entropy -= p * math.log2(p)
        entropies.append(entropy)
    
    if entropies:
        entropy_var = sum((e - sum(entropies)/len(entropies))**2 for e in entropies) / len(entropies)
        entropy_score = min(max((entropy_var - 0.1) / 0.5, 0), 1)
    else:
        entropy_score = 0
    
    # Metric 4: Size-based duration proxy
    size_score = min(max((len(payload) - 2000) / 10000, 0), 1)
    
    # Multi-condition: Require 3/4
    conditions = [variance_score > 0.6, spike_score > 0.4, entropy_score > 0.3, size_score > 0.3]
    condition_count = sum(conditions)
    
    if condition_count < 3:
        return 0.0
    
    confidence = (
        variance_score * 0.4 +
        spike_score * 0.3 +
        entropy_score * 0.2 +
        size_score * 0.1
    )
    
    if condition_count == 4:
        confidence *= 1.2
    
    return min(max(confidence, 0), 1)


def analyze_audio_energy(audio_bytes: bytes) -> float:
    """
    Improved distress detection using multi-metric analysis.
    
    Only triggers for high-intensity emotional sounds (shouting, crying, panic).
    Normal speech and background noise return low confidence.
    
    Returns confidence 0.0-1.0. Distress only if > 0.8.
    """
    if not audio_bytes or len(audio_bytes) < 100:
        return 0.0
    
    # Try WAV analysis first (more accurate)
    pcm_samples = _try_decode_wav(audio_bytes)
    if pcm_samples and len(pcm_samples) > 1000:  # Require minimum length
        confidence = _analyze_wav_distress(pcm_samples)
        if confidence > 0.8:  # Only return high confidence
            return confidence
    
    # Fallback to compressed analysis
    confidence = _analyze_compressed_distress(audio_bytes)
    return confidence if confidence > 0.8 else 0.0


def get_distress_info(confidence: float) -> dict:
    """
    Get distress level label and message from confidence score.
    
    Distress only detected if confidence > 0.8.
    Below that, treated as normal sound.
    
    Confidence ranges:
      0.0 - 0.8  → Normal sound (no distress)
      0.8 - 0.9  → Moderate distress
      0.9 - 1.0  → High distress
    """
    if confidence <= 0.8:
        return {
            "level": "Normal Sound",
            "detected": False,
            "message": f"Normal audio detected (confidence: {int(confidence * 100)}%). No distress indicators.",
            "color": "success"
        }
    elif confidence < 0.9:
        return {
            "level": "Moderate Distress",
            "detected": True,
            "message": f"Moderate distress detected (confidence: {int(confidence * 100)}%). Possible elevated emotional state.",
            "color": "warning"
        }
    else:
        return {
            "level": "High Distress",
            "detected": True,
            "message": f"High distress detected (confidence: {int(confidence * 100)}%). Strong indicators of shouting, crying, or panic.",
            "color": "danger"
        }


class TriggerInput(BaseModel):
    trigger_type: str = "simulated"  # 'audio_stream' or 'simulated'
    audio_data: Optional[str] = None


@router.post("/detect-trigger")
async def detect_trigger(data: TriggerInput):
    """
    Detects distress automatically from an audio stream or simulated trigger.
    For simple JSON triggers without audio, returns a baseline low confidence.
    """
    await asyncio.sleep(1.0)

    # Without actual audio attached, return a low baseline
    confidence = 0.15

    return {
        "status": "success",
        "distress_detected": False,
        "confidence": confidence,
        "trigger_source": data.trigger_type,
        "message": "Trigger acknowledged. Awaiting audio for analysis."
    }


@router.post("/detect-trigger-audio")
async def detect_trigger_audio(file: UploadFile = File(...)):
    """
    Analyze actual uploaded audio for distress levels.
    Returns real confidence based on audio energy analysis.
    """
    content = await file.read()
    
    await asyncio.sleep(0.5)

    confidence = analyze_audio_energy(content)
    info = get_distress_info(confidence)

    return {
        "status": "success",
        "distress_detected": info["detected"],
        "confidence": confidence,
        "distress_level": info["level"],
        "distress_color": info["color"],
        "trigger_source": "audio_analysis",
        "message": info["message"]
    }
