# ======================================================================
# H-S50-C — Explicit local valve catalogue loader
# ======================================================================

from __future__ import annotations

import json
import math
from pathlib import Path

from HVAC.hydronics_v3.dto.valve_catalog_dto import (
    ValveCatalogDTO,
    ValveKvOptionDTO,
)


LOCAL_VALVE_CATALOGUE_SCHEMA_V1 = "local_valve_catalogue_v1"
LOCAL_GENERIC_VALVE_CATALOGUE_PATH_V1 = Path(__file__).with_name(
    "local_generic_valve_catalogue_v1.json"
)


def load_local_valve_catalogue_v1(path: str | Path) -> ValveCatalogDTO:
    """Load one explicit local JSON catalogue as non-authoritative evidence."""

    source_path = Path(path)
    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Local valve catalogue cannot be read: {source_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Local valve catalogue JSON is invalid: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError("Local valve catalogue root must be an object")
    if str(raw.get("schema") or "").strip() != LOCAL_VALVE_CATALOGUE_SCHEMA_V1:
        raise ValueError(
            f"Local valve catalogue schema must be {LOCAL_VALVE_CATALOGUE_SCHEMA_V1}"
        )

    catalog_id = str(raw.get("catalog_id") or "").strip()
    if not catalog_id:
        raise ValueError("Local valve catalogue catalog_id is required")

    raw_options = raw.get("kv_options")
    if not isinstance(raw_options, list) or not raw_options:
        raise ValueError("Local valve catalogue requires at least one kv_options row")

    options: list[ValveKvOptionDTO] = []
    seen_refs: set[str] = set()
    for index, raw_option in enumerate(raw_options, start=1):
        if not isinstance(raw_option, dict):
            raise ValueError(f"Local valve catalogue option {index} must be an object")
        valve_ref = str(raw_option.get("valve_ref") or "").strip()
        if not valve_ref:
            raise ValueError(f"Local valve catalogue option {index} requires valve_ref")
        if valve_ref in seen_refs:
            raise ValueError(f"Duplicate local valve catalogue valve_ref: {valve_ref}")
        seen_refs.add(valve_ref)

        kv = _positive_finite_v1(raw_option.get("kv_m3_h"))
        if kv is None:
            raise ValueError(
                f"Positive finite kv_m3_h required for local valve {valve_ref}"
            )
        options.append(
            ValveKvOptionDTO(
                valve_ref=valve_ref,
                kv_m3_h=kv,
                note=str(raw_option.get("note") or "").strip(),
            )
        )

    return ValveCatalogDTO(catalog_id=catalog_id, kv_options=options)


def load_bundled_local_valve_catalogue_v1() -> ValveCatalogDTO:
    """Load HVACgooee's explicit local generic evidence catalogue."""

    return load_local_valve_catalogue_v1(
        LOCAL_GENERIC_VALVE_CATALOGUE_PATH_V1
    )


def _positive_finite_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0.0 else None
