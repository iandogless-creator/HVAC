"""
template_geometry_engine_v1.py
------------------------------

HVACgooee — Template Geometry Engine v1

Purpose
-------
Provide simple, deterministic footprint generators for early-stage heat-loss projects.

v1 Rules
--------
- Generates 2D footprints only (polygon in world meters).
- No adjacency, no room graph, no constraints, no editing.
- One template -> one footprint polygon.
- Output polygon is closed implicitly (first point NOT repeated at end).
- Coordinate frame: (0,0) is local origin; +x east, +y north.

Templates (v1)
--------------
1) RECT
   - width_m, depth_m

2) L_SHAPE
   - width_m, depth_m
   - cutout_width_m, cutout_depth_m
   The "cutout" is removed from the top-right corner by default.

3) MEZZ
   - footprint: RECT (width_m, depth_m)
   - mezzanine: mezz_depth_m (from the "north/top" edge), plus optional mezz_height_m
   Returns footprint polygon + mezz metadata (no 3D solids).

This module does NOT depend on Project/Space models.
It is safe to call from GUI, controllers, or future engines.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

Point = Tuple[float, float]


class TemplateKind(str, Enum):
    RECT = "rect"
    L_SHAPE = "l_shape"
    MEZZ = "mezz"


@dataclass(frozen=True)
class RectParams:
    width_m: float
    depth_m: float


@dataclass(frozen=True)
class LShapeParams:
    width_m: float
    depth_m: float
    cutout_width_m: float
    cutout_depth_m: float


@dataclass(frozen=True)
class MezzParams:
    width_m: float
    depth_m: float
    mezz_depth_m: float
    mezz_height_m: Optional[float] = None


TemplateParams = Union[RectParams, LShapeParams, MezzParams]


@dataclass(frozen=True)
class TemplateGeometryResult:
    kind: TemplateKind
    footprint: List[Point]
    meta: Dict[str, object]


def _require_positive(name: str, v: float) -> None:
    if v is None or not isinstance(v, (int, float)):
        raise ValueError(f"{name} must be a number.")
    if v <= 0.0:
        raise ValueError(f"{name} must be > 0. Got: {v}")


def _require_non_negative(name: str, v: float) -> None:
    if v is None or not isinstance(v, (int, float)):
        raise ValueError(f"{name} must be a number.")
    if v < 0.0:
        raise ValueError(f"{name} must be >= 0. Got: {v}")


def polygon_area_m2(poly: List[Point]) -> float:
    if len(poly) < 3:
        return 0.0
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return abs(s) * 0.5


def make_rect(params: RectParams) -> List[Point]:
    _require_positive("width_m", params.width_m)
    _require_positive("depth_m", params.depth_m)

    w = float(params.width_m)
    d = float(params.depth_m)

    return [
        (0.0, 0.0),
        (w, 0.0),
        (w, d),
        (0.0, d),
    ]


def make_l_shape(params: LShapeParams) -> List[Point]:
    _require_positive("width_m", params.width_m)
    _require_positive("depth_m", params.depth_m)
    _require_non_negative("cutout_width_m", params.cutout_width_m)
    _require_non_negative("cutout_depth_m", params.cutout_depth_m)

    w = float(params.width_m)
    d = float(params.depth_m)
    cw = float(params.cutout_width_m)
    cd = float(params.cutout_depth_m)

    if cw <= 0.0 or cd <= 0.0:
        return make_rect(RectParams(width_m=w, depth_m=d))

    if cw >= w or cd >= d:
        raise ValueError(
            "L_SHAPE cutout must be smaller than the main rectangle. "
            f"Got width={w}, depth={d}, cutout_width={cw}, cutout_depth={cd}"
        )

    x_cut = w - cw
    y_cut = d - cd

    return [
        (0.0, 0.0),
        (w, 0.0),
        (w, y_cut),
        (x_cut, y_cut),
        (x_cut, d),
        (0.0, d),
    ]


def make_mezz(params: MezzParams) -> TemplateGeometryResult:
    _require_positive("width_m", params.width_m)
    _require_positive("depth_m", params.depth_m)
    _require_non_negative("mezz_depth_m", params.mezz_depth_m)
    if params.mezz_height_m is not None:
        _require_positive("mezz_height_m", float(params.mezz_height_m))

    w = float(params.width_m)
    d = float(params.depth_m)
    md = float(params.mezz_depth_m)

    if md > d:
        raise ValueError(
            f"mezz_depth_m cannot exceed depth_m. Got mezz_depth_m={md}, depth_m={d}"
        )

    footprint = make_rect(RectParams(width_m=w, depth_m=d))

    meta: Dict[str, object] = {
        "mezzanine": {
            "present": md > 0.0,
            "zone": "north_band",
            "mezz_depth_m": md,
            "mezz_height_m": float(params.mezz_height_m) if params.mezz_height_m is not None else None,
            "mezz_area_m2": w * md,
            "mezz_fraction_of_floor": (w * md) / (w * d) if (w * d) > 0 else 0.0,
            "bounds": {
                "min_x": 0.0,
                "min_y": d - md,
                "max_x": w,
                "max_y": d,
            },
        }
    }

    return TemplateGeometryResult(kind=TemplateKind.MEZZ, footprint=footprint, meta=meta)


def generate_template_geometry(kind: TemplateKind, params: TemplateParams) -> TemplateGeometryResult:
    if kind == TemplateKind.RECT:
        if not isinstance(params, RectParams):
            raise TypeError("RECT requires RectParams.")
        poly = make_rect(params)
        return TemplateGeometryResult(
            kind=TemplateKind.RECT,
            footprint=poly,
            meta={"area_m2": polygon_area_m2(poly)},
        )

    if kind == TemplateKind.L_SHAPE:
        if not isinstance(params, LShapeParams):
            raise TypeError("L_SHAPE requires LShapeParams.")
        poly = make_l_shape(params)
        return TemplateGeometryResult(
            kind=TemplateKind.L_SHAPE,
            footprint=poly,
            meta={
                "area_m2": polygon_area_m2(poly),
                "cutout": {
                    "cutout_width_m": float(params.cutout_width_m),
                    "cutout_depth_m": float(params.cutout_depth_m),
                    "corner": "top_right",
                },
            },
        )

    if kind == TemplateKind.MEZZ:
        if not isinstance(params, MezzParams):
            raise TypeError("MEZZ requires MezzParams.")
        res = make_mezz(params)
        area = polygon_area_m2(res.footprint)
        meta = dict(res.meta)
        meta["area_m2"] = area
        return TemplateGeometryResult(kind=res.kind, footprint=res.footprint, meta=meta)

    raise ValueError(f"Unsupported template kind: {kind}")


def to_space_polygon(result: TemplateGeometryResult) -> List[Point]:
    return list(result.footprint)
