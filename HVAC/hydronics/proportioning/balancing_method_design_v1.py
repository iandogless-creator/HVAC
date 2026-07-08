# ======================================================================
# HVAC/hydronics/proportioning/balancing_method_design_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


NONE_REQUIRED = "NONE_REQUIRED"
PROPORTIONAL_ADDED_RESISTANCE = "PROPORTIONAL_ADDED_RESISTANCE"
LOCKSHIELD_THROTTLING_PREVIEW = "LOCKSHIELD_THROTTLING_PREVIEW"
DPCV_ZONE_PREVIEW = "DPCV_ZONE_PREVIEW"
PICV_EMITTER_PREVIEW = "PICV_EMITTER_PREVIEW"
MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


_DEFAULT_METHOD_ID_V1 = PROPORTIONAL_ADDED_RESISTANCE

_EXCLUSIONS_V1: tuple[str, ...] = (
    "No valve product selected",
    "No Kv or Kvs selected",
    "No lockshield turn count",
    "No pump selected",
    "No final balancing",
    "No pipe resizing",
    "No ProjectState mutation",
)


@dataclass(frozen=True, slots=True)
class BalancingMethodOptionV1:
    """
    H-S31-A:
    Balancing method design option.

    This defines method intent only. It does not size or select a valve.
    """

    method_id: str
    label: str
    allowed_in_v1: bool
    status: str
    input_basis: str
    output_boundary: str
    note: str = ""


@dataclass(frozen=True, slots=True)
class BalancingMethodDesignModelV1:
    """
    H-S31-A:
    Balancing method design model.

    Design authority only:
        no valve product selected
        no Kv / Kvs selected
        no lockshield turn count
        no pump selected
        no final balancing
        no pipe resizing
        no ProjectState mutation
    """

    schema: str = "balancing_method_design_model_v1"
    ready: bool = False
    selected_method_id: str = _DEFAULT_METHOD_ID_V1
    selected_method_label: str = ""
    status: str = ""
    blockers: tuple[str, ...] = ()
    options: tuple[BalancingMethodOptionV1, ...] = ()
    exclusions: tuple[str, ...] = _EXCLUSIONS_V1
    note: str = (
        "Balancing method design model only — no valve sizing, "
        "pump selection, pipe resizing, or final balancing."
    )


def build_balancing_method_options_v1() -> tuple[BalancingMethodOptionV1, ...]:
    return (
        BalancingMethodOptionV1(
            method_id=NONE_REQUIRED,
            label="None required",
            allowed_in_v1=True,
            status="Allowed when route has no added resistance requirement",
            input_basis="Controlling route or zero shortfall evidence",
            output_boundary="Reports no added resistance requirement",
            note="Does not prove final balance; only records no preview burden.",
        ),
        BalancingMethodOptionV1(
            method_id=PROPORTIONAL_ADDED_RESISTANCE,
            label="Proportional added resistance",
            allowed_in_v1=True,
            status="Default v1 balancing method candidate",
            input_basis=(
                "Required added Δp, route flow kg/s, and provisional "
                "resistance Pa/(kg/s)²"
            ),
            output_boundary=(
                "Identifies required added resistance only; no valve selected"
            ),
            note=(
                "This is the natural next step from the current provisional "
                "burden table."
            ),
        ),
        BalancingMethodOptionV1(
            method_id=LOCKSHIELD_THROTTLING_PREVIEW,
            label="Lockshield throttling preview",
            allowed_in_v1=False,
            status="Deferred — needs valve authority / setting model",
            input_basis="Valve data, emitter flow, and acceptable authority",
            output_boundary="Would preview throttling intent only",
            note="No turn-count calculation in H-S31-A.",
        ),
        BalancingMethodOptionV1(
            method_id=DPCV_ZONE_PREVIEW,
            label="DPCV zone preview",
            allowed_in_v1=False,
            status="Deferred — needs zone/group authority model",
            input_basis="Zone grouping, design Δp target, and DPCV assumptions",
            output_boundary="Would preview zone control intent only",
        ),
        BalancingMethodOptionV1(
            method_id=PICV_EMITTER_PREVIEW,
            label="PICV emitter preview",
            allowed_in_v1=False,
            status="Deferred — needs PICV valve data and emitter authority",
            input_basis="Emitter flow, valve family, minimum Δp, and authority",
            output_boundary="Would preview PICV suitability only",
        ),
        BalancingMethodOptionV1(
            method_id=MANUAL_REVIEW_REQUIRED,
            label="Manual review required",
            allowed_in_v1=True,
            status="Allowed fallback when automatic method is unsuitable",
            input_basis="Incomplete or unsuitable route burden evidence",
            output_boundary="Reports blocker / manual review reason",
        ),
    )


def build_balancing_method_design_model_v1(
        *,
        selected_method_id: str = _DEFAULT_METHOD_ID_V1,
) -> BalancingMethodDesignModelV1:
    """
    Build H-S31-A balancing method design model.

    Pure model builder:
        no ProjectState mutation
        no GUI dependency
        no valve sizing
        no pump sizing
        no final balancing
    """
    options = build_balancing_method_options_v1()
    options_by_id = {
        option.method_id: option
        for option in options
    }

    blockers: list[str] = []

    selected = options_by_id.get(selected_method_id)

    if selected is None:
        selected = options_by_id[MANUAL_REVIEW_REQUIRED]
        blockers.append(f"Unknown balancing method: {selected_method_id}")
    elif not selected.allowed_in_v1:
        blockers.append(
            f"Balancing method deferred in v1: {selected.method_id}"
        )

    ready = not blockers

    status = (
        f"Ready — balancing method design selected: {selected.label}"
        if ready
        else "Blocked — " + "; ".join(blockers)
    )

    return BalancingMethodDesignModelV1(
        ready=ready,
        selected_method_id=selected.method_id,
        selected_method_label=selected.label,
        status=status,
        blockers=tuple(blockers),
        options=options,
    )


def balancing_method_design_model_to_dict_v1(
        model: BalancingMethodDesignModelV1 | None,
) -> dict[str, Any] | None:
    if model is None:
        return None

    return {
        "schema": model.schema,
        "ready": model.ready,
        "selected_method_id": model.selected_method_id,
        "selected_method_label": model.selected_method_label,
        "status": model.status,
        "blockers": tuple(model.blockers),
        "options": tuple(asdict(option) for option in model.options),
        "exclusions": tuple(model.exclusions),
        "note": model.note,
    }
