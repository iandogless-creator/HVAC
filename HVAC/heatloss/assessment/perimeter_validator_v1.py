# ======================================================================
# HVAC/heatloss/assessment/perimeter_validator_v1.py
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable


TOLERANCE_M = 0.005  # 5 mm tolerance


@dataclass(frozen=True, slots=True)
class PerimeterValidationResult:
    room_id: str
    declared_perimeter_m: float
    summed_boundary_length_m: float
    difference_m: float
    is_valid: bool


def validate_room_perimeter(
    *,
    room_id: str,
    declared_perimeter_m: float,
    boundary_lengths: Iterable[float],
) -> PerimeterValidationResult:

    total = sum(float(l) for l in boundary_lengths)
    diff = total - float(declared_perimeter_m)
    is_valid = abs(diff) <= TOLERANCE_M

    return PerimeterValidationResult(
        room_id=room_id,
        declared_perimeter_m=float(declared_perimeter_m),
        summed_boundary_length_m=total,
        difference_m=diff,
        is_valid=is_valid,
    )