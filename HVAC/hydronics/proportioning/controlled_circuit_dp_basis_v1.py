# ======================================================================
# HVAC/hydronics/proportioning/controlled_circuit_dp_basis_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


CONTROLLED_CIRCUIT_DP_UNRESOLVED = "CONTROLLED_CIRCUIT_DP_UNRESOLVED"
ROUTE_CHOSEN_DP = "ROUTE_CHOSEN_DP"
ROUTE_CHOSEN_DP_MINUS_REQUIRED_ADDED_DP = (
    "ROUTE_CHOSEN_DP_MINUS_REQUIRED_ADDED_DP"
)
MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


_DEFAULT_BASIS_ID_V1 = ROUTE_CHOSEN_DP

_EXCLUSIONS_V1: tuple[str, ...] = (
    "No authority ratio calculated",
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
class ControlledCircuitDpBasisOptionV1:
    """
    H-S32-E:
    Controlled-circuit Δp basis option.

    Basis definition only. This does not calculate valve authority.
    """

    basis_id: str
    label: str
    allowed_in_v1: bool
    status: str
    formula: str
    note: str = ""


@dataclass(frozen=True, slots=True)
class ControlledCircuitDpBasisModelV1:
    """
    H-S32-E:
    Controlled-circuit Δp basis model.

    Design basis only:
        no authority ratio calculated
        no valve product selected
        no Kv / Kvs selected
        no lockshield turn count
        no manufacturer valve data
        no pump selected
        no final balancing
        no pipe resizing
        no ProjectState mutation
    """

    schema: str = "controlled_circuit_dp_basis_model_v1"
    ready: bool = False
    selected_basis_id: str = _DEFAULT_BASIS_ID_V1
    selected_basis_label: str = ""
    status: str = ""
    blockers: tuple[str, ...] = ()
    options: tuple[ControlledCircuitDpBasisOptionV1, ...] = ()
    exclusions: tuple[str, ...] = _EXCLUSIONS_V1
    note: str = (
        "Controlled-circuit Δp basis model only — no authority ratio, "
        "no valve sizing, no Kv/Kvs, and no final balancing."
    )


@dataclass(frozen=True, slots=True)
class ControlledCircuitDpResolutionV1:
    """
    H-S32-E:
    Scalar controlled-circuit Δp resolution.

    Resolves only controlled_circuit_dp_pa from a declared basis.
    It does not calculate authority.
    """

    basis_id: str = _DEFAULT_BASIS_ID_V1
    ready: bool = False
    controlled_circuit_dp_pa: float | None = None
    status: str = ""
    blockers: tuple[str, ...] = ()
    note: str = ""


def build_controlled_circuit_dp_basis_options_v1(
) -> tuple[ControlledCircuitDpBasisOptionV1, ...]:
    return (
        ControlledCircuitDpBasisOptionV1(
            basis_id=CONTROLLED_CIRCUIT_DP_UNRESOLVED,
            label="Unresolved",
            allowed_in_v1=True,
            status="Allowed placeholder until route pressure basis is available",
            formula="controlled_circuit_dp_pa = None",
            note="Used before authority preview is allowed.",
        ),
        ControlledCircuitDpBasisOptionV1(
            basis_id=ROUTE_CHOSEN_DP,
            label="Route chosen Δp",
            allowed_in_v1=True,
            status="Default v1 basis",
            formula="controlled_circuit_dp_pa = route_chosen_dp_pa",
            note=(
                "Uses the existing chosen-basis route pressure drop before "
                "added balancing burden."
            ),
        ),
        ControlledCircuitDpBasisOptionV1(
            basis_id=ROUTE_CHOSEN_DP_MINUS_REQUIRED_ADDED_DP,
            label="Route chosen Δp minus required added Δp",
            allowed_in_v1=True,
            status="Alternative diagnostic basis",
            formula=(
                "controlled_circuit_dp_pa = "
                "route_chosen_dp_pa - required_added_dp_pa"
            ),
            note=(
                "Useful only when the supplied route Δp already includes "
                "the theoretical added balancing burden."
            ),
        ),
        ControlledCircuitDpBasisOptionV1(
            basis_id=MANUAL_REVIEW_REQUIRED,
            label="Manual review required",
            allowed_in_v1=True,
            status="Required when pressure basis is missing or unsuitable",
            formula="controlled_circuit_dp_pa = None",
            note="Fallback only; no authority calculation.",
        ),
    )


def build_controlled_circuit_dp_basis_model_v1(
        *,
        selected_basis_id: str = _DEFAULT_BASIS_ID_V1,
) -> ControlledCircuitDpBasisModelV1:
    options = build_controlled_circuit_dp_basis_options_v1()
    options_by_id = {
        option.basis_id: option
        for option in options
    }

    blockers: list[str] = []
    selected = options_by_id.get(selected_basis_id)

    if selected is None:
        selected = options_by_id[MANUAL_REVIEW_REQUIRED]
        blockers.append(f"Unknown controlled-circuit Δp basis: {selected_basis_id}")
    elif not selected.allowed_in_v1:
        blockers.append(
            f"Controlled-circuit Δp basis deferred in v1: {selected.basis_id}"
        )

    ready = not blockers

    status = (
        f"Ready — controlled-circuit Δp basis selected: {selected.label}"
        if ready
        else "Blocked — " + "; ".join(blockers)
    )

    return ControlledCircuitDpBasisModelV1(
        ready=ready,
        selected_basis_id=selected.basis_id,
        selected_basis_label=selected.label,
        status=status,
        blockers=tuple(blockers),
        options=options,
    )


def _positive_number_v1(
        value: object,
        *,
        label: str,
        blockers: list[str],
        allow_zero: bool = False,
) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        blockers.append(f"{label} required")
        return None

    if allow_zero:
        if number < 0.0:
            blockers.append(f"{label} must be zero or greater")
            return None
    elif number <= 0.0:
        blockers.append(f"{label} must be greater than zero")
        return None

    return number


def resolve_controlled_circuit_dp_v1(
        *,
        basis_id: str = _DEFAULT_BASIS_ID_V1,
        route_chosen_dp_pa: object = None,
        required_added_dp_pa: object = None,
) -> ControlledCircuitDpResolutionV1:
    """
    Resolve controlled_circuit_dp_pa from the selected H-S32-E basis.

    Scalar basis resolution only:
        no authority ratio calculated
        no valve product selected
        no Kv / Kvs selected
        no final balancing
    """
    blockers: list[str] = []

    if basis_id == CONTROLLED_CIRCUIT_DP_UNRESOLVED:
        return ControlledCircuitDpResolutionV1(
            basis_id=basis_id,
            ready=False,
            controlled_circuit_dp_pa=None,
            status="Blocked — controlled-circuit Δp basis unresolved",
            blockers=("Controlled-circuit Δp basis unresolved",),
            note="Authority preview must wait for a selected pressure basis.",
        )

    if basis_id == MANUAL_REVIEW_REQUIRED:
        return ControlledCircuitDpResolutionV1(
            basis_id=basis_id,
            ready=False,
            controlled_circuit_dp_pa=None,
            status="Manual review required — no controlled-circuit Δp resolved",
            blockers=("Manual review required",),
            note="Fallback only; no authority calculation.",
        )

    route_dp = _positive_number_v1(
        route_chosen_dp_pa,
        label="Route chosen Δp",
        blockers=blockers,
    )

    if basis_id == ROUTE_CHOSEN_DP:
        if blockers:
            return ControlledCircuitDpResolutionV1(
                basis_id=basis_id,
                ready=False,
                controlled_circuit_dp_pa=None,
                status="Blocked — " + "; ".join(blockers),
                blockers=tuple(blockers),
            )

        return ControlledCircuitDpResolutionV1(
            basis_id=basis_id,
            ready=True,
            controlled_circuit_dp_pa=route_dp,
            status="Ready — controlled-circuit Δp resolved from route chosen Δp",
            blockers=(),
            note="No authority ratio calculated in H-S32-E.",
        )

    if basis_id == ROUTE_CHOSEN_DP_MINUS_REQUIRED_ADDED_DP:
        added_dp = _positive_number_v1(
            required_added_dp_pa,
            label="Required added Δp",
            blockers=blockers,
            allow_zero=True,
        )

        if not blockers and route_dp is not None and added_dp is not None:
            controlled_dp = route_dp - added_dp

            if controlled_dp <= 0.0:
                blockers.append(
                    "Route chosen Δp minus required added Δp must be greater than zero"
                )
            else:
                return ControlledCircuitDpResolutionV1(
                    basis_id=basis_id,
                    ready=True,
                    controlled_circuit_dp_pa=controlled_dp,
                    status=(
                        "Ready — controlled-circuit Δp resolved from route "
                        "chosen Δp minus required added Δp"
                    ),
                    blockers=(),
                    note="No authority ratio calculated in H-S32-E.",
                )

        return ControlledCircuitDpResolutionV1(
            basis_id=basis_id,
            ready=False,
            controlled_circuit_dp_pa=None,
            status="Blocked — " + "; ".join(blockers),
            blockers=tuple(blockers),
        )

    return ControlledCircuitDpResolutionV1(
        basis_id=MANUAL_REVIEW_REQUIRED,
        ready=False,
        controlled_circuit_dp_pa=None,
        status=f"Blocked — unknown controlled-circuit Δp basis: {basis_id}",
        blockers=(f"Unknown controlled-circuit Δp basis: {basis_id}",),
    )


def controlled_circuit_dp_basis_model_to_dict_v1(
        model: ControlledCircuitDpBasisModelV1 | None,
) -> dict[str, Any] | None:
    if model is None:
        return None

    return {
        "schema": model.schema,
        "ready": model.ready,
        "selected_basis_id": model.selected_basis_id,
        "selected_basis_label": model.selected_basis_label,
        "status": model.status,
        "blockers": tuple(model.blockers),
        "options": tuple(asdict(option) for option in model.options),
        "exclusions": tuple(model.exclusions),
        "note": model.note,
    }


def controlled_circuit_dp_resolution_to_dict_v1(
        resolution: ControlledCircuitDpResolutionV1 | None,
) -> dict[str, Any] | None:
    if resolution is None:
        return None

    return {
        "basis_id": resolution.basis_id,
        "ready": resolution.ready,
        "controlled_circuit_dp_pa": resolution.controlled_circuit_dp_pa,
        "status": resolution.status,
        "blockers": tuple(resolution.blockers),
        "note": resolution.note,
    }
