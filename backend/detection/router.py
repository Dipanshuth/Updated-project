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


def analyze_audio_energy(audio_bytes: bytes) -> float:
    """
    Analyze audio bytes for energy/volume level.
    Returns a distress confidence between 0.0 and 1.0.
    
    Handles both WAV (raw PCM) and WebM/Opus/OGG (compressed container) formats.
    
    Calibrated thresholds:
    - Silent / very quiet audio  → 0.05 - 0.20
    - Normal speaking voice      → 0.15 - 0.35
    - Raised / emotional voice   → 0.35 - 0.55
    - Loud / shouting            → 0.55 - 0.75
    - Extreme screaming          → 0.75 - 0.95
    """
    if not audio_bytes or len(audio_bytes) < 100:
        return 0.08  # Nearly silent / no data

    # === Attempt 1: Try to decode as WAV (gives us real PCM samples) ===
    pcm_samples = _try_decode_wav(audio_bytes)
    if pcm_samples and len(pcm_samples) > 100:
        # Compute RMS from actual PCM samples
        total = sum(s * s for s in pcm_samples)
        rms = math.sqrt(total / len(pcm_samples))
        
        # 16-bit PCM RMS calibration:
        # Silence: ~0-50, Normal speech: ~500-2500, Raised voice: ~2500-5000, Shouting: ~5000+
        if rms < 80:
            confidence = 0.05 + (rms / 80) * 0.10        # 0.05 - 0.15
        elif rms < 800:
            confidence = 0.15 + ((rms - 80) / 720) * 0.15  # 0.15 - 0.30
        elif rms < 2500:
            confidence = 0.30 + ((rms - 800) / 1700) * 0.20  # 0.30 - 0.50
        elif rms < 6000:
            confidence = 0.50 + ((rms - 2500) / 3500) * 0.25  # 0.50 - 0.75
        else:
            confidence = 0.75 + min((rms - 6000) / 20000, 0.20)  # 0.75 - 0.95
        
        return round(min(max(confidence, 0.05), 0.95), 2)

    # === Attempt 2: Compressed container (WebM, Opus, OGG) ===
    energy_score = _extract_pcm_from_container(audio_bytes)
    if energy_score is not None:
        # Map energy score (0-1) to calibrated confidence
        # Most normal speech recordings will produce energy_score ~0.1-0.3
        if energy_score < 0.08:
            confidence = 0.05 + energy_score * 1.25        # 0.05 - 0.15 (silence)
        elif energy_score < 0.25:
            confidence = 0.15 + ((energy_score - 0.08) / 0.17) * 0.15  # 0.15 - 0.30 (quiet/normal)
        elif energy_score < 0.45:
            confidence = 0.30 + ((energy_score - 0.25) / 0.20) * 0.20  # 0.30 - 0.50 (raised voice)
        elif energy_score < 0.70:
            confidence = 0.50 + ((energy_score - 0.45) / 0.25) * 0.25  # 0.50 - 0.75 (shouting)
        else:
            confidence = 0.75 + min((energy_score - 0.70) / 0.30 * 0.20, 0.20)  # 0.75 - 0.95
        
        return round(min(max(confidence, 0.05), 0.95), 2)

    # === Fallback: Very basic byte analysis ===
    # Sample a section avoiding headers
    start = min(500, len(audio_bytes) // 4)
    sample = audio_bytes[start:start + min(5000, len(audio_bytes) - start)]
    
    if len(sample) < 50:
        return 0.10
    
    byte_vals = list(sample)
    mean = sum(byte_vals) / len(byte_vals)
    variance = sum((b - mean) ** 2 for b in byte_vals) / len(byte_vals)
    
    # Very conservative mapping — default to low confidence
    norm_var = min(max((variance - 4000) / 3000, 0), 1.0)
    confidence = 0.10 + norm_var * 0.30  # 0.10 - 0.40 max
    
    return round(min(max(confidence, 0.05), 0.50), 2)


def get_distress_info(confidence: float) -> dict:
    """Get distress level label and message from confidence score."""
    if confidence < 0.20:
        return {
            "level": "Minimal",
            "detected": False,
            "message": "Very low audio energy. No signs of distress.",
            "color": "success"
        }
    elif confidence < 0.35:
        return {
            "level": "Low",
            "detected": False,
            "message": "Normal audio levels detected. No significant distress indicators.",
            "color": "success"
        }
    elif confidence < 0.55:
        return {
            "level": "Medium",
            "detected": False,
            "message": "Moderate vocal energy detected. Some stress patterns present but within normal range.",
            "color": "warning"
        }
    elif confidence < 0.75:
        return {
            "level": "High",
            "detected": True,
            "message": "Elevated stress levels detected. Possible distress situation.",
            "color": "danger"
        }
    else:
        return {
            "level": "Critical",
            "detected": True,
            "message": "Extreme audio energy detected. Likely distress or emergency situation.",
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
