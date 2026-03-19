import hashlib
import json


def compute_checksum(payload: dict) -> str:
    """
    Deterministic SHA-256 checksum of payload.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()