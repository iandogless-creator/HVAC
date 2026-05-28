# ======================================================================
# HVAC/hydronics/sizing/basic_ps_pressure_preview_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from HVAC.hydronics.sizing.basic_ps_pipe_sizing_v1 import (
    BasicPSPipeSizingResultV1,
)


# ======================================================================
# DTOs
# ======================================================================

@dataclass(frozen=True, slots=True)
class BasicPSPressurePreviewRowV1:
    """
    Read-only Basic PS section pressure preview row.

    H-S8-H:
    Uses an existing Basic PS pressure gradient and an optional section
    length to preview section Δp.

    This is not final proportioning or balancing.
    """

    section_id: str
    order: int
    from_label: str
    to_room_label: str

    pressure_gradient_Pa_per_m: float
    section_length_m: float | None
    section_pressure_drop_Pa: float | None

    is_index_room: bool = False
    is_terminal: bool = False
    status: str = "Length not set"


@dataclass(frozen=True, slots=True)
class BasicPSPressurePreviewProjectionV1:
    """
    Read-only Basic PS section pressure preview projection.

    Does not:
    - mutate ProjectState
    - invent section lengths
    - account for fittings, tees, valves, or balancing
    - select the controlling index route
    """

    rows: tuple[BasicPSPressurePreviewRowV1, ...]
    total_pressure_drop_Pa: float | None
    status: str = "Preview only"


# ======================================================================
# Public builder
# ======================================================================

def build_basic_ps_pressure_preview_v1(
    sizing_results: Iterable[BasicPSPipeSizingResultV1],
    *,
    section_lengths_m: dict[str, float] | None = None,
) -> BasicPSPressurePreviewProjectionV1:
    """
    Build Basic PS pressure preview rows.

    section_lengths_m:
        Optional mapping:
            section_id -> length in metres

    If a section has no length, its section Δp remains None.
    """

    lengths = section_lengths_m or {}
    rows: list[BasicPSPressurePreviewRowV1] = []

    total_pressure_drop_Pa = 0.0
    has_missing_lengths = False

    for result in sizing_results:
        section_length_m = _normalise_optional_positive_float(
            lengths.get(result.section_id)
        )

        if section_length_m is None:
            section_pressure_drop_Pa = None
            status = "Length not set"
            has_missing_lengths = True
        else:
            section_pressure_drop_Pa = (
                result.pressure_gradient_Pa_per_m * section_length_m
            )
            total_pressure_drop_Pa += section_pressure_drop_Pa
            status = "Preview only"

        rows.append(
            BasicPSPressurePreviewRowV1(
                section_id=result.section_id,
                order=result.order,
                from_label=result.from_label,
                to_room_label=result.to_room_label,
                pressure_gradient_Pa_per_m=result.pressure_gradient_Pa_per_m,
                section_length_m=section_length_m,
                section_pressure_drop_Pa=section_pressure_drop_Pa,
                is_index_room=result.is_index_room,
                is_terminal=result.is_terminal,
                status=status,
            )
        )

    resolved_total = None if has_missing_lengths else total_pressure_drop_Pa

    return BasicPSPressurePreviewProjectionV1(
        rows=tuple(rows),
        total_pressure_drop_Pa=resolved_total,
        status=(
            "Preview incomplete — section length missing"
            if has_missing_lengths
            else "Preview only"
        ),
    )


# ======================================================================
# Helpers
# ======================================================================

def _normalise_optional_positive_float(value: object) -> float | None:
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if number <= 0.0:
        return None

    return number