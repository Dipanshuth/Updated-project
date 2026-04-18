"""Test the full upload + analysis pipeline using only stdlib"""
import urllib.request
import urllib.parse
import json
import os
import uuid

BASE = "http://localhost:8000"

def post_json(url, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def get_json(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())

def multipart_upload(url, filepath, filename, fields=None):
    boundary = uuid.uuid4().hex
    lines = []
    # Add form fields
    if fields:
        for key, val in fields.items():
            lines.append(f"--{boundary}".encode())
            lines.append(f'Content-Disposition: form-data; name="{key}"'.encode())
            lines.append(b"")
            lines.append(val.encode())
    # Add file
    with open(filepath, "rb") as f:
        file_data = f.read()
    lines.append(f"--{boundary}".encode())
    lines.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode())
    lines.append(b"Content-Type: audio/wav")
    lines.append(b"")
    lines.append(file_data)
    lines.append(f"--{boundary}--".encode())
    
    body = b"\r\n".join(lines)
    req = urllib.request.Request(url, data=body)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# 1. Upload
print("=== 1. UPLOADING TEST AUDIO ===")
upload = multipart_upload(
    f"{BASE}/evidence/upload",
    "test_normal_speech.wav",
    "test_normal_speech.wav",
    {"description": "Test normal speech", "datetime": "2026-04-17T14:30:00", "location": "Test Lab", "latitude": "28.6139", "longitude": "77.2090"}
)
evidence_id = upload["evidence_id"]
print(f"  Evidence ID: {evidence_id}")
print(f"  Status: {upload.get('status')}")

# 2. Analyze
print("\n=== 2. ANALYZING EVIDENCE ===")
analysis = post_json(f"{BASE}/evidence/{evidence_id}/analyze", {})
print(f"  Confidence: {analysis.get('confidence_pct')}%")
print(f"  Distress Level: {analysis.get('distress_level')}")
print(f"  Distress Detected: {analysis.get('distress')}")

# 3. Detect-trigger-audio
print("\n=== 3. DETECT-TRIGGER-AUDIO ===")
detect = multipart_upload(f"{BASE}/detect-trigger-audio", "test_normal_speech.wav", "test.wav")
print(f"  Confidence: {round(detect.get('confidence', 0) * 100)}%")
print(f"  Distress Level: {detect.get('distress_level')}")
print(f"  Detected: {detect.get('distress_detected')}")
print(f"  Message: {detect.get('message')}")

# 4. Run inference
print("\n=== 4. RUN INFERENCE ===")
infer = post_json(f"{BASE}/run-inference", {"evidence_id": evidence_id})
print(f"  Classification: {infer.get('distress_classification')}")
print(f"  Confidence: {round(infer.get('confidence', 0) * 100)}%")

# 5. Detail
print("\n=== 5. EVIDENCE DETAIL ===")
detail = get_json(f"{BASE}/evidence/{evidence_id}/detail")
print(f"  Status: {detail.get('status')}")
print(f"  Confidence: {detail.get('confidence_pct')}%")
print(f"  Level: {detail.get('distress_level')}")

# 6. List
print("\n=== 6. EVIDENCE LIST ===")
listing = get_json(f"{BASE}/evidence/list")
print(f"  Total records: {len(listing['evidence'])}")
for e in listing["evidence"]:
    print(f"    - {e['id']}: status={e['status']}, confidence={e.get('confidence')}%")

print("\n=== ALL TESTS PASSED ===")
