#!/usr/bin/env python3
"""
Test script for the enhanced distress detection system.
This demonstrates the new multi-metric analysis with confidence scoring.
"""

import math
import struct
import wave
import os
from backend.detection.router import analyze_audio_energy, get_distress_info

def create_test_audio_samples():
    """Create synthetic audio samples for testing"""
    samples = {}

    # Normal conversation (low amplitude, steady)
    normal_samples = []
    for i in range(44100):  # 1 second at 44.1kHz
        # Low amplitude sine wave with some variation
        sample = int(3000 * math.sin(2 * math.pi * 300 * i / 44100) + 500 * math.sin(2 * math.pi * 50 * i / 44100))
        normal_samples.append(max(-32767, min(32767, sample)))

    # Shouting (high amplitude, spikes)
    shouting_samples = []
    for i in range(44100):
        # High amplitude with spikes
        base = 20000 * math.sin(2 * math.pi * 400 * i / 44100)
        # Add random spikes
        if i % 500 == 0:
            base += 10000 * (1 if i % 1000 == 0 else -1)
        shouting_samples.append(int(max(-32767, min(32767, base))))

    # Background noise (very low amplitude)
    noise_samples = []
    for i in range(44100):
        noise_samples.append(int(500 * math.sin(2 * math.pi * 100 * i / 44100)))

    samples['normal'] = normal_samples
    samples['shouting'] = shouting_samples
    samples['noise'] = noise_samples

    return samples

def test_distress_detection():
    """Test the distress detection with different audio types"""
    print("🧪 Testing Enhanced Distress Detection System")
    print("=" * 50)

    samples = create_test_audio_samples()

    test_cases = [
        ("Normal Conversation", samples['normal']),
        ("Shouting/Screaming", samples['shouting']),
        ("Background Noise", samples['noise'])
    ]

    for name, audio_samples in test_cases:
        # Convert to bytes (16-bit PCM)
        audio_bytes = b''
        for sample in audio_samples:
            audio_bytes += struct.pack('<h', sample)

        # Add WAV header
        wav_data = create_wav_header(len(audio_bytes)) + audio_bytes

        # Analyze
        confidence = analyze_audio_energy(wav_data)
        distress_info = get_distress_info(confidence)

        print(f"\n📊 {name}:")
        print(".2f")
        print(f"   Level: {distress_info['level']}")
        print(f"   Detected: {distress_info['detected']}")
        print(f"   Message: {distress_info['message']}")

def create_wav_header(data_size):
    """Create a minimal WAV header"""
    header = b'RIFF'
    header += (36 + data_size).to_bytes(4, 'little')  # File size
    header += b'WAVE'
    header += b'fmt '
    header += (16).to_bytes(4, 'little')  # Format chunk size
    header += (1).to_bytes(2, 'little')   # PCM format
    header += (1).to_bytes(2, 'little')   # Mono
    header += (44100).to_bytes(4, 'little')  # Sample rate
    header += (88200).to_bytes(4, 'little')  # Byte rate
    header += (2).to_bytes(2, 'little')   # Block align
    header += (16).to_bytes(2, 'little')  # Bits per sample
    header += b'data'
    header += data_size.to_bytes(4, 'little')
    return header

if __name__ == "__main__":
    test_distress_detection()