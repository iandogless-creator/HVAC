# ======================================================================
# HVAC/hydronics/proportioning/valve_authority_design_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


VALVE_AUTHORITY_NONE_REQUIRED = "VALVE_AUTHORITY_NONE_REQUIRED"
VALVE_AUTHORITY_INPUT_AVAILABLE = "VALVE_AUTHORITY_INPUT_AVAILABLE"
TOO_LOW_AUTHORITY_PREVIEW = "TOO_LOW_AUTHORITY_PREVIEW"
ACCEPTABLE_AUTHORITY_PREVIEW = "ACCEPTABLE_AUTHORITY_PREVIEW"
HIGH_THROTTLING_BURDEN = "HIGH_THROTTLING_BURDEN"
MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


_DEFAULT_MINIMUM_AUTHORITY_V1 = 0.25
_DEFAULT_HIGH_THROTTLING_AUTHORITY_V1 = 0.70

_AUTHORITY_FORMULA_V1 = (
    "authority = design_valve_dp_pa / "
    "(design_valve_dp_pa + controlled_circuit_dp_pa)"
)

_EXCLUSIONS_V1: tuple[str, ...] = (
    "No valve product selected",
    "No Kv or Kvs selected",
    "No lockshield turn count",
    "No manufacturer valve data",
    "No pump selected",
    "No final balancing",
    "No pipe resizing",
    "No ProjectState mutation",
)


@dataclass(frozen=True, slots=True)
class ValveAuthorityBandV1:
    """
    H-S32-A:
    Valve authority design band.

    Band definition only. This does not select or size a valve.
    """

    band_id: str
    label: str
    minimum_authority: float | None
    maximum_authority: float | None
    allowed_in_v1: bool
    status: str
    note: str = ""


@dataclass(frozen=True, slots=True)
class ValveAuthorityDesignModelV1:
    """
    H-S32-A:
    Valve authority design model.

    Design authority only:
        no valve product selected
        no Kv / Kvs selected
        no lockshield turn count
        no manufacturer valve data
        no pump selected
        no final balancing
        no pipe resizing
        no ProjectState mutation
    """

    schema: str = "valve_authority_design_model_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()

    minimum_authority: float = _DEFAULT_MINIMUM_AUTHORITY_V1
    high_throttling_authority: float = _DEFAULT_HIGH_THROTTLING_AUTHORITY_V1
    authority_formula: str = _AUTHORITY_FORMULA_V1

    design_valve_dp_basis: str = (
        "Future H-S32 mapping uses required added Δp as theoretical "
        "design valve/throttling Δp."
    )
    controlled_circuit_dp_basis: str = (
        "Future H-S32 mapping must provide the associated controlled "
        "circuit Δp before authority can be classified."
    )

    bands: tuple[ValveAuthorityBandV1, ...] = ()
    exclusions: tuple[str, ...] = _EXCLUSIONS_V1
    note: str = (
        "Valve authority design model only — no valve sizing, no Kv/Kvs, "
        "no valve product selection, no pump selection, and no final balancing."
    )


def build_valve_authority_bands_v1(
        *,
        minimum_authority: float = _DEFAULT_MINIMUM_AUTHORITY_V1,
        high_throttling_authority: float = _DEFAULT_HIGH_THROTTLING_AUTHORITY_V1,
) -> tuple[ValveAuthorityBandV1, ...]:
    return (
        ValveAuthorityBandV1(
            band_id=VALVE_AUTHORITY_NONE_REQUIRED,
            label="No valve authority required",
            minimum_authority=None,
            maximum_authority=None,
            allowed_in_v1=True,
            status="Allowed when no added balancing resistance is required",
            note=(
                "Used for controlling or zero-burden routes; does not prove "
                "final hydraulic balance."
            ),
        ),
        ValveAuthorityBandV1(
            band_id=VALVE_AUTHORITY_INPUT_AVAILABLE,
            label="Valve authority input available",
            minimum_authority=None,
            maximum_authority=None,
            allowed_in_v1=True,
            status="Allowed when required added Δp is available but authority is not yet classified",
            note=(
                "This is a design-input state, not a valve selection result."
            ),
        ),
        ValveAuthorityBandV1(
            band_id=TOO_LOW_AUTHORITY_PREVIEW,
            label="Too low authority preview",
            minimum_authority=0.0,
            maximum_authority=minimum_authority,
            allowed_in_v1=True,
            status="Preview warning — valve authority below minimum design threshold",
            note=(
                "Later mapping may use this as a warning/blocker before "
                "valve selection."
            ),
        ),
        ValveAuthorityBandV1(
            band_id=ACCEPTABLE_AUTHORITY_PREVIEW,
            label="Acceptable authority preview",
            minimum_authority=minimum_authority,
            maximum_authority=high_throttling_authority,
            allowed_in_v1=True,
            status="Preview acceptable band — still no valve selected",
            note=(
                "Acceptable band only; manufacturer data and Kv/Kvs are not "
                "included."
            ),
        ),
        ValveAuthorityBandV1(
            band_id=HIGH_THROTTLING_BURDEN,
            label="High throttling burden",
            minimum_authority=high_throttling_authority,
            maximum_authority=1.0,
            allowed_in_v1=True,
            status="Preview warning — throttling burden is high",
            note=(
                "High authority may indicate excessive throttling burden; "
                "manual review or different design method may be required."
            ),
        ),
        ValveAuthorityBandV1(
            band_id=MANUAL_REVIEW_REQUIRED,
            label="Manual review required",
            minimum_authority=None,
            maximum_authority=None,
            allowed_in_v1=True,
            status="Required when authority inputs are missing or unsuitable",
            note="Fallback only; no valve selection.",
        ),
    )


def _threshold_blockers_v1(
        *,
        minimum_authority: float,
        high_throttling_authority: float,
) -> tuple[str, ...]:
    blockers: list[str] = []

    if minimum_authority <= 0.0:
        blockers.append("Minimum authority must be greater than zero")

    if minimum_authority >= 1.0:
        blockers.append("Minimum authority must be less than one")

    if high_throttling_authority <= 0.0:
        blockers.append("High throttling authority must be greater than zero")

    if high_throttling_authority > 1.0:
        blockers.append("High throttling authority must be no greater than one")

    if minimum_authority >= high_throttling_authority:
        blockers.append(
            "Minimum authority must be lower than high throttling authority"
        )

    return tuple(blockers)


def classify_valve_authority_band_v1(
        authority: float | None,
        *,
        minimum_authority: float = _DEFAULT_MINIMUM_AUTHORITY_V1,
        high_throttling_authority: float = _DEFAULT_HIGH_THROTTLING_AUTHORITY_V1,
) -> str:
    """
    Classify an already-calculated authority ratio.

    Scalar classification only:
        no valve sizing
        no Kv/Kvs
        no manufacturer data
        no final balancing
    """
    if authority is None:
        return MANUAL_REVIEW_REQUIRED

    try:
        value = float(authority)
    except (TypeError, ValueError):
        return MANUAL_REVIEW_REQUIRED

    if value < 0.0 or value > 1.0:
        return MANUAL_REVIEW_REQUIRED

    if value < minimum_authority:
        return TOO_LOW_AUTHORITY_PREVIEW

    if value <= high_throttling_authority:
        return ACCEPTABLE_AUTHORITY_PREVIEW

    return HIGH_THROTTLING_BURDEN


def build_valve_authority_design_model_v1(
        *,
        minimum_authority: float = _DEFAULT_MINIMUM_AUTHORITY_V1,
        high_throttling_authority: float = _DEFAULT_HIGH_THROTTLING_AUTHORITY_V1,
) -> ValveAuthorityDesignModelV1:
    """
    Build H-S32-A valve authority design model.

    Pure model builder:
        no ProjectState mutation
        no GUI dependency
        no valve product selection
        no Kv / Kvs selection
        no lockshield turns
        no pump sizing
        no final balancing
    """
    blockers = _threshold_blockers_v1(
        minimum_authority=minimum_authority,
        high_throttling_authority=high_throttling_authority,
    )

    ready = not blockers

    status = (
        "Ready — valve authority design model available"
        if ready
        else "Blocked — " + "; ".join(blockers)
    )

    return ValveAuthorityDesignModelV1(
        ready=ready,
        status=status,
        blockers=blockers,
        minimum_authority=minimum_authority,
        high_throttling_authority=high_throttling_authority,
        bands=build_valve_authority_bands_v1(
            minimum_authority=minimum_authority,
            high_throttling_authority=high_throttling_authority,
        ),
    )


def valve_authority_design_model_to_dict_v1(
        model: ValveAuthorityDesignModelV1 | None,
) -> dict[str, Any] | None:
    if model is None:
        return None

    return {
        "schema": model.schema,
        "ready": model.ready,
        "status": model.status,
        "blockers": tuple(model.blockers),
        "minimum_authority": model.minimum_authority,
        "high_throttling_authority": model.high_throttling_authority,
        "authority_formula": model.authority_formula,
        "design_valve_dp_basis": model.design_valve_dp_basis,
        "controlled_circuit_dp_basis": model.controlled_circuit_dp_basis,
        "bands": tuple(asdict(band) for band in model.bands),
        "exclusions": tuple(model.exclusions),
        "note": model.note,
    }
