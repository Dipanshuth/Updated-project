"""
AI Digital Memory Vault — Hash Service
SHA-256 hashing for evidence integrity verification
"""

import hashlib


def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hash from raw bytes."""
    return hashlib.sha256(data).hexdigest()


def verify_hash(file_path: str, expected_hash: str) -> bool:
    """Verify file integrity by comparing hashes."""
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash


def generate_blockchain_anchor(file_hash: str) -> dict:
    """
    Mock blockchain anchoring.
    Phase 2: Integrate with actual blockchain/timestamping service.
    """
    return {
        "hash": file_hash,
        "blockchain_anchored": True,
        "block_number": 48291,
        "anchored_at": "2026-04-16T14:32:15Z",
        "chain": "mock-chain",
    }
