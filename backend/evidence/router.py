import os
import hashlib
import uuid
import json
import math
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from models import SessionLocal, Evidence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

router = APIRouter(tags=["Evidence"])


def _fetch_json(url: str, headers: dict | None = None, timeout: int = 10):
    request = Request(url, headers=headers or {})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
        return json.loads(payload)


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_police_query(lat: float, lng: float) -> str:
    return f"""
[out:json][timeout:12];
(
  node(around:7000,{lat},{lng})["amenity"="police"];
  way(around:7000,{lat},{lng})["amenity"="police"];
  relation(around:7000,{lat},{lng})["amenity"="police"];
  node(around:7000,{lat},{lng})["office"="police"];
  way(around:7000,{lat},{lng})["office"="police"];
  relation(around:7000,{lat},{lng})["office"="police"];
);
out center tags;
""".strip()


def _find_nearest_police_station(lat: float, lng: float) -> dict | None:
    query = _build_police_query(lat, lng)
    url = "https://overpass-api.de/api/interpreter?" + urlencode({"data": query})
    try:
        data = _fetch_json(url, headers={"User-Agent": "AI-Digital-Memory-Vault/1.0"}, timeout=12)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    best_match = None
    best_distance = None
    best_named_match = None
    best_named_distance = None
    keywords = ("police", "station", "thana", "ps", "थाना")

    for element in data.get("elements", []):
        element_lat = element.get("lat") or element.get("center", {}).get("lat")
        element_lng = element.get("lon") or element.get("center", {}).get("lon")
        if element_lat is None or element_lng is None:
            continue

        distance_km = _haversine_km(lat, lng, float(element_lat), float(element_lng))
        tags = element.get("tags", {})
        raw_name = tags.get("name") or tags.get("official_name") or tags.get("operator") or tags.get("brand") or ""
        address = ", ".join(
            part for part in [
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
                tags.get("addr:suburb"),
                tags.get("addr:city"),
            ] if part
        )
        station_name = raw_name.strip()
        station_lower = station_name.lower()
        looks_like_station = any(keyword in station_lower for keyword in keywords)

        candidate = {
            "name": station_name,
            "distance_km": round(distance_km, 2),
            "address": address or station_name,
        }

        if looks_like_station and (best_named_distance is None or distance_km < best_named_distance):
            best_named_distance = distance_km
            best_named_match = candidate

        if best_distance is None or distance_km < best_distance:
            best_distance = distance_km
            best_match = candidate

    if best_named_match:
        return best_named_match

    if best_match:
        best_match["name"] = "Nearest Police Station"
        return best_match

    # Fallback: search Nominatim within a local bounding box for police stations.
    bbox = f"{lng - 0.08},{lat - 0.08},{lng + 0.08},{lat + 0.08}"
    search_url = "https://nominatim.openstreetmap.org/search?" + urlencode({
        "q": "police station",
        "format": "jsonv2",
        "limit": 10,
        "bounded": 1,
        "viewbox": bbox,
        "addressdetails": 1,
    })

    try:
        search_results = _fetch_json(search_url, headers={"User-Agent": "AI-Digital-Memory-Vault/1.0"}, timeout=12)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        search_results = []

    best_search_match = None
    best_search_distance = None
    for result in search_results:
        result_lat = result.get("lat")
        result_lng = result.get("lon")
        if result_lat is None or result_lng is None:
            continue

        distance_km = _haversine_km(lat, lng, float(result_lat), float(result_lng))
        if best_search_distance is None or distance_km < best_search_distance:
            best_search_distance = distance_km
            best_search_match = {
                "name": result.get("name") or result.get("display_name") or "Nearest Police Station",
                "distance_km": round(distance_km, 2),
                "address": result.get("display_name") or result.get("name") or "",
            }

    if best_search_match:
        return best_search_match

    return None


@router.get("/resolve-location")
async def resolve_location(lat: float, lng: float):
    """Resolve coordinates into a readable address and nearest police station."""
    reverse_params = urlencode({
        "format": "jsonv2",
        "lat": lat,
        "lon": lng,
        "zoom": 18,
        "addressdetails": 1,
    })
    reverse_url = f"https://nominatim.openstreetmap.org/reverse?{reverse_params}"

    resolved_address = None
    address_parts = {}

    try:
        reverse_data = _fetch_json(
            reverse_url,
            headers={"User-Agent": "AI-Digital-Memory-Vault/1.0"},
            timeout=12,
        )
        resolved_address = reverse_data.get("display_name")
        address_parts = reverse_data.get("address", {}) or {}
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        resolved_address = None

    police_station = _find_nearest_police_station(lat, lng)

    if not resolved_address:
        resolved_address = f"{lat:.6f}, {lng:.6f}"

    return {
        "status": "success",
        "latitude": lat,
        "longitude": lng,
        "resolved_address": resolved_address,
        "nearest_police_station": police_station["name"] if police_station else None,
        "nearest_police_station_distance_km": police_station["distance_km"] if police_station else None,
        "nearest_police_station_address": police_station["address"] if police_station else None,
        "city": address_parts.get("city") or address_parts.get("town") or address_parts.get("village") or "",
        "state": address_parts.get("state") or "",
        "country": address_parts.get("country") or "",
        "source": "OpenStreetMap Nominatim + Overpass",
    }

@router.post("/upload-evidence")
async def upload_evidence(
    file: UploadFile = File(...),
    gps_data: str = Form(""),
    timestamp: str = Form(""),
    device_id: str = Form(""),
):
    """
    Accepts audio file, GPS data, timestamp, and device ID. 
    Stores securely (local storage) and tracks in DB.
    """
    evidence_id = f"EVD-{str(uuid.uuid4())[:8].upper()}"
    os.makedirs("uploads", exist_ok=True)
    
    file_path = os.path.join("uploads", f"{evidence_id}_{file.filename}")
    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    file_hash = hashlib.sha256(content).hexdigest()

    db = SessionLocal()
    try:
        # Parsing GPS if available (e.g. "28.6139, 77.2090")
        lat = ""
        lng = ""
        if gps_data and "," in gps_data:
            lat, lng = [part.strip() for part in gps_data.split(",", 1)]

        evidence = Evidence(
            evidence_id=evidence_id,
            filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            file_type=file.content_type or "audio/unknown",
            sha256_hash=file_hash,
            description=f"Automated upload from device {device_id}",
            incident_datetime=timestamp or datetime.utcnow().isoformat(),
            location=gps_data,
            latitude=lat,
            longitude=lng,
            status="pending",
            created_at=datetime.utcnow().isoformat(),
        )
        db.add(evidence)
        db.commit()
    finally:
        db.close()

    return {
        "status": "success",
        "evidence_id": evidence_id,
        "hash": file_hash,
        "message": "Evidence uploaded securely."
    }

@router.get("/verify-integrity")
async def verify_integrity(evidence_id: str):
    """
    Checks the tamper-evident storage for the hash.
    Generates SHA-256 hash or returns existing securely stored one.
    """
    db = SessionLocal()
    try:
        record = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        # Verify if file still exists and hash matches
        verification_status = "intact"
        if os.path.exists(record.file_path):
            with open(record.file_path, "rb") as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
                if current_hash != record.sha256_hash:
                    verification_status = "tampered"
        else:
            verification_status = "file_missing"

        return {
            "evidence_id": evidence_id,
            "stored_hash": record.sha256_hash,
            "verification_status": verification_status,
            "algorithm": "SHA-256",
            "message": f"Integrity check: {verification_status}"
        }
    finally:
        db.close()
