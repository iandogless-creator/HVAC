# ======================================================================
# HVAC/dev/export_hydronic_20_room_multileg_project.py
# ======================================================================

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)


def _checksum_payload(payload: dict) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    project = build_hydronic_20_room_multileg_project_v1()

    project_dir = Path("HVAC/HVACprojects/20 room multileg")
    project_dir.mkdir(parents=True, exist_ok=True)

    project.project_dir = str(project_dir)

    payload = project.to_dict()

    wrapped = {
        "checksum": _checksum_payload(payload),
        "payload": payload,
        "schema_version": payload.get("schema_version", 4),
    }

    path = project_dir / "project.json"
    path.write_text(
        json.dumps(wrapped, indent=4, sort_keys=True),
        encoding="utf-8",
    )

    print("Wrote:", path)
    print("Rooms:", len(project.rooms))
    print("Emitters:", len(project.emitters))
    print("Topology:", bool(getattr(project, "hydronic_topology", None)))
    print("Local K:", bool(getattr(project, "hydronic_local_k_intent", None)))


if __name__ == "__main__":
    main()
