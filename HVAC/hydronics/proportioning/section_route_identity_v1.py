# ======================================================================
# HVAC/hydronics/proportioning/section_route_identity_v1.py
# ======================================================================

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class SectionRouteIdentityV1:
    """
    Best-effort route identity for a Basic PS section row.

    This does not model branch take-off points.
    Branch subleg take-off remains TBA in v1.
    """

    route_code: str = ""
    leg_id: str = ""
    subleg_id: str = ""
    route_id: str = ""
    subleg_role: str = ""
    takeoff_status: str = ""


def _text(value: object) -> str:
    return str(value or "").strip()


def _route_code_from_label(value: object) -> str:
    """
    Extract codes like L1A, L1B, L2A, L2B from labels such as:
        L1A-R01
        R5 L2B-R05
    """
    text = _text(value).upper()
    match = re.search(r"\bL\d+[A-Z]\b", text)
    if not match:
        return ""
    return match.group(0)


def _leg_id_from_section_id(section_id: str) -> str:
    match = re.search(r"\b(leg-\d+)\b", section_id)
    if not match:
        return ""
    return match.group(1)


def _subleg_id_from_section_id(section_id: str) -> str:
    marker = "-section-"
    if marker not in section_id:
        return ""
    return section_id.split(marker, 1)[0]


def infer_section_route_identity_v1(row: dict) -> SectionRouteIdentityV1:
    """
    Infer route/subleg identity from the section row currently produced
    by Basic PS.

    Important:
    • This is identity only.
    • It does not model branch take-off positions.
    • Branch take-off remains TBA.
    """
    row = row or {}

    section_id = _text(row.get("section_id"))

    route_code = (
        _route_code_from_label(row.get("to"))
        or _route_code_from_label(row.get("from"))
    )

    leg_id = _leg_id_from_section_id(section_id)
    subleg_id = _subleg_id_from_section_id(section_id)

    subleg_role = ""
    takeoff_status = ""

    if "primary-subleg" in subleg_id:
        subleg_role = "common"
    elif "subleg" in subleg_id:
        subleg_role = "branch"
        takeoff_status = "TBA"

    route_id = subleg_id or route_code

    return SectionRouteIdentityV1(
        route_code=route_code,
        leg_id=leg_id,
        subleg_id=subleg_id,
        route_id=route_id,
        subleg_role=subleg_role,
        takeoff_status=takeoff_status,
    )


def enrich_basic_ps_section_rows_with_route_identity_v1(
    rows: list[dict],
) -> list[dict]:
    """
    Return section rows enriched with route/subleg identity where it can
    be inferred safely.
    """
    enriched_rows: list[dict] = []

    for row in rows or []:
        new_row = dict(row or {})
        identity = infer_section_route_identity_v1(new_row)

        new_row.setdefault("route_code", identity.route_code)
        new_row.setdefault("leg_id", identity.leg_id)
        new_row.setdefault("subleg_id", identity.subleg_id)
        new_row.setdefault("route_id", identity.route_id)
        new_row.setdefault("subleg_role", identity.subleg_role)
        new_row.setdefault("takeoff_status", identity.takeoff_status)

        enriched_rows.append(new_row)

    return enriched_rows