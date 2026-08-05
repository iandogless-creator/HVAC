# ======================================================================
# H-S66-N1A — Environment universal pipe-pair spacing defaults
# ======================================================================

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

MOULDED_PLASTIC_DOUBLE_CLIP_V1 = "moulded_plastic_double_clip"
PAIRED_INDIVIDUAL_PLASTIC_CLIPS_V1 = "paired_individual_plastic_clips"
DOUBLE_MUNSEN_RING_V1 = "double_munsen_ring"

# H-S66-L schema values are accepted as data here without importing the
# arrangement authority into Environment persistence.
STACKED_FLOW_RETURN_PAIR_V1 = "stacked_flow_return_pair"
SEPARATE_PIPE_V1 = "separate_pipe"

PIPE_PAIR_SUPPORT_LABELS_V1 = {
    MOULDED_PLASTIC_DOUBLE_CLIP_V1: "Moulded plastic double clip",
    PAIRED_INDIVIDUAL_PLASTIC_CLIPS_V1: "Paired individual plastic clips",
    DOUBLE_MUNSEN_RING_V1: "Double Munsen ring / bracket",
}

STACKED_PIPE_PAIR_NOMINAL_OD_MM_V1 = (10, 15, 22, 28, 35, 42, 54)

# Representative domestic installation defaults. They deliberately represent
# nominal support geometry rather than one manufacturer's exact dimensions.
# Small make-to-make dimensional differences are not product-selection data.
_DEFAULT_ROWS_V1 = (
    (10, MOULDED_PLASTIC_DOUBLE_CLIP_V1, 25.0),
    (15, MOULDED_PLASTIC_DOUBLE_CLIP_V1, 30.0),
    (22, MOULDED_PLASTIC_DOUBLE_CLIP_V1, 40.0),
    (28, PAIRED_INDIVIDUAL_PLASTIC_CLIPS_V1, 50.0),
    (35, PAIRED_INDIVIDUAL_PLASTIC_CLIPS_V1, 60.0),
    (42, PAIRED_INDIVIDUAL_PLASTIC_CLIPS_V1, 70.0),
    (54, PAIRED_INDIVIDUAL_PLASTIC_CLIPS_V1, 90.0),
)


@dataclass(frozen=True, slots=True)
class EnvironmentPipePairSpacingDefaultV1:
    nominal_outside_diameter_mm: int
    support_type: str
    support_label: str
    centre_spacing_mm: float
    source: str = "Environment universal stacked-pair spacing default"


def default_environment_pipe_pair_spacing_defaults_v1() -> dict[str, dict]:
    """Return a fresh JSON-compatible default mapping."""

    return {
        str(size): {
            "support_type": support_type,
            "centre_spacing_mm": spacing,
        }
        for size, support_type, spacing in _DEFAULT_ROWS_V1
    }


def normalise_environment_pipe_pair_spacing_defaults_v1(
        raw_defaults: object,
) -> dict[str, dict]:
    """Validate a complete universal mapping without silently filling rows."""

    if not isinstance(raw_defaults, Mapping):
        raise ValueError("Pipe-pair spacing defaults mapping is required")

    expected = {str(size) for size in STACKED_PIPE_PAIR_NOMINAL_OD_MM_V1}
    supplied = {str(key).strip() for key in raw_defaults}
    if supplied != expected:
        missing = sorted(expected - supplied, key=int)
        extra = sorted(supplied - expected)
        detail: list[str] = []
        if missing:
            detail.append("missing " + ", ".join(missing) + " mm")
        if extra:
            detail.append("unsupported " + ", ".join(extra) + " mm")
        raise ValueError("Pipe-pair spacing defaults are incomplete: " + "; ".join(detail))

    clean: dict[str, dict] = {}
    for size in STACKED_PIPE_PAIR_NOMINAL_OD_MM_V1:
        value = raw_defaults.get(str(size), raw_defaults.get(size))
        if not isinstance(value, Mapping):
            raise ValueError(f"{size} mm pipe-pair spacing default is required")
        support_type = str(value.get("support_type", "")).strip()
        if support_type not in PIPE_PAIR_SUPPORT_LABELS_V1:
            raise ValueError(f"{size} mm pipe-pair support type is unsupported")
        try:
            spacing = float(value.get("centre_spacing_mm"))
        except (TypeError, ValueError):
            raise ValueError(f"{size} mm pipe-pair c/c is required") from None
        if spacing <= float(size):
            raise ValueError(f"{size} mm pipe-pair c/c must exceed pipe OD")
        if spacing > 500.0:
            raise ValueError(f"{size} mm pipe-pair c/c exceeds 500 mm")
        clean[str(size)] = {
            "support_type": support_type,
            "centre_spacing_mm": spacing,
        }
    return clean


def resolve_environment_pipe_pair_spacing_default_v1(
        *,
        raw_defaults: object,
        nominal_outside_diameter_mm: object,
        external_arrangement: object,
) -> EnvironmentPipePairSpacingDefaultV1 | None:
    """Resolve one default only for an H-S66-L stacked pipe pair."""

    arrangement = str(external_arrangement or "").strip()
    if arrangement == SEPARATE_PIPE_V1:
        return None
    if arrangement != STACKED_FLOW_RETURN_PAIR_V1:
        raise ValueError("Committed pipe external arrangement is unsupported")
    try:
        size = int(nominal_outside_diameter_mm)
    except (TypeError, ValueError):
        raise ValueError("Nominal pipe outside diameter is required") from None
    if size not in STACKED_PIPE_PAIR_NOMINAL_OD_MM_V1:
        raise ValueError(f"Unsupported stacked pipe nominal OD: {size} mm")
    clean = normalise_environment_pipe_pair_spacing_defaults_v1(raw_defaults)
    row = clean[str(size)]
    support_type = str(row["support_type"])
    return EnvironmentPipePairSpacingDefaultV1(
        nominal_outside_diameter_mm=size,
        support_type=support_type,
        support_label=PIPE_PAIR_SUPPORT_LABELS_V1[support_type],
        centre_spacing_mm=float(row["centre_spacing_mm"]),
    )
