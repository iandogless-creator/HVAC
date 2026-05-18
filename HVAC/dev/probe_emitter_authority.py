# ======================================================================
# HVAC/dev/probe_emitter_authority.py
# ======================================================================

from __future__ import annotations

"""
HVACgooee — Hydronics H-O Probe
Emitter authority / room-emitter map

Purpose
-------
Print the current room/emitter truth from ProjectState.

This probe is deliberately read-only:
• no ProjectState mutation
• no default emitter creation
• no hydronic sizing
• no GUI dependency
"""

from typing import Any


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _fmt(value: Any, fallback: str = "—") -> str:
    if value is None:
        return fallback
    text = str(value)
    return text if text else fallback


def _fmt_w(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.1f} W"
    except (TypeError, ValueError):
        return str(value)


def _fmt_temp(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.1f} °C"
    except (TypeError, ValueError):
        return str(value)


def _room_name(room: Any, room_id: str) -> str:
    return (
        getattr(room, "name", None)
        or getattr(room, "room_name", None)
        or room_id
    )


def _emitter_room_id(emitter: Any) -> str | None:
    return getattr(emitter, "room_id", None)


def _emitter_id(emitter: Any, fallback: str) -> str:
    return (
        getattr(emitter, "emitter_id", None)
        or fallback
    )


def _emitter_type(emitter: Any) -> str:
    return (
        getattr(emitter, "emitter_type", None)
        or getattr(emitter, "type", None)
        or "—"
    )


def _emitter_output_W(emitter: Any) -> Any:
    return (
        getattr(emitter, "design_output_W", None)
        or getattr(emitter, "output_W", None)
        or getattr(emitter, "nominal_output_W", None)
    )


def _emitter_flow_temp_C(emitter: Any) -> Any:
    return getattr(emitter, "flow_temp_C", None)


def _emitter_return_temp_C(emitter: Any) -> Any:
    return getattr(emitter, "return_temp_C", None)


def _build_emitters_by_room(project_state: Any) -> tuple[dict[str, list[Any]], list[tuple[str, Any]]]:
    emitters_by_room: dict[str, list[Any]] = {}
    orphan_emitters: list[tuple[str, Any]] = []

    rooms = getattr(project_state, "rooms", {}) or {}
    emitters = getattr(project_state, "emitters", {}) or {}

    for emitter_key, emitter in emitters.items():
        room_id = _emitter_room_id(emitter)

        if not room_id:
            orphan_emitters.append((str(emitter_key), emitter))
            continue

        if room_id not in rooms:
            orphan_emitters.append((str(emitter_key), emitter))
            continue

        emitters_by_room.setdefault(room_id, []).append(emitter)

    return emitters_by_room, orphan_emitters


def print_emitter_authority(project_state: Any) -> None:
    rooms = getattr(project_state, "rooms", {}) or {}
    emitters = getattr(project_state, "emitters", {}) or {}

    emitters_by_room, orphan_emitters = _build_emitters_by_room(project_state)

    print()
    print("=" * 100)
    print("HVACgooee — Hydronics H-O Probe")
    print("Emitter authority / room-emitter map")
    print("=" * 100)
    print()
    print(f"Rooms:    {len(rooms)}")
    print(f"Emitters: {len(emitters)}")
    print()

    header = (
        f"{'Room ID':<12} "
        f"{'Room name':<22} "
        f"{'Emitter ID':<30} "
        f"{'Type':<12} "
        f"{'Output':>12} "
        f"{'FT':>10} "
        f"{'RT':>10} "
        f"{'Status':<20}"
    )

    print(header)
    print("-" * len(header))

    for room_id, room in rooms.items():
        room_emitters = emitters_by_room.get(room_id, [])
        room_name = _room_name(room, room_id)

        if not room_emitters:
            print(
                f"{room_id:<12} "
                f"{room_name:<22} "
                f"{'—':<30} "
                f"{'—':<12} "
                f"{'—':>12} "
                f"{'—':>10} "
                f"{'—':>10} "
                f"{'NO_EMITTER':<20}"
            )
            continue

        for index, emitter in enumerate(room_emitters):
            emitter_id = _emitter_id(emitter, f"<missing-id-{index}>")
            emitter_type = _emitter_type(emitter)
            output_W = _emitter_output_W(emitter)
            flow_temp_C = _emitter_flow_temp_C(emitter)
            return_temp_C = _emitter_return_temp_C(emitter)

            status = "OK"
            if len(room_emitters) > 1:
                status = "MULTIPLE_EMITTERS"

            print(
                f"{room_id:<12} "
                f"{room_name:<22} "
                f"{emitter_id:<30} "
                f"{emitter_type:<12} "
                f"{_fmt_w(output_W):>12} "
                f"{_fmt_temp(flow_temp_C):>10} "
                f"{_fmt_temp(return_temp_C):>10} "
                f"{status:<20}"
            )

    if orphan_emitters:
        print()
        print("Orphan emitters")
        print("-" * 100)

        for emitter_key, emitter in orphan_emitters:
            emitter_id = _emitter_id(emitter, emitter_key)
            room_id = _emitter_room_id(emitter)

            print(
                f"{'—':<12} "
                f"{'—':<22} "
                f"{emitter_id:<30} "
                f"{_emitter_type(emitter):<12} "
                f"{_fmt_w(_emitter_output_W(emitter)):>12} "
                f"{_fmt_temp(_emitter_flow_temp_C(emitter)):>10} "
                f"{_fmt_temp(_emitter_return_temp_C(emitter)):>10} "
                f"ORPHAN room_id={_fmt(room_id)}"
            )

    print()
    print("=" * 100)
    print("Probe complete")
    print("=" * 100)
    print()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> None:
    import json
    from pathlib import Path

    from HVAC.project.project_state import ProjectState

    path = Path("HVAC/HVACprojects/clean_4_room_identity_test/project.json")

    if not path.exists():
        raise SystemExit(f"Project file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    payload = data.get("payload", data)

    project_state = ProjectState.from_dict(payload)

    print_emitter_authority(project_state)

if __name__ == "__main__":
    main()