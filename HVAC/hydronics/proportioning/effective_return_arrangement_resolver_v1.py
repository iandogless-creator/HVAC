"""
H-S27-A — effective return arrangement resolver.

Purpose:
    Resolve the user design-basis return arrangement hierarchy into the
    effective arrangement used by Proportioning.

Hierarchy:
    System
        -> Leg
            -> Common subleg
                -> Branch subleg

Semantics:
    INHERIT means "use parent effective basis".
    DIRECT_RETURN means F&R.
    REVERSE_RETURN means F+RR.

Important:
    This is Proportioning input authority only.
    No pump sizing.
    No valve selection.
    No balancing mutation.
    No pipe resizing.
    No final Proportioned result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DIRECT_RETURN = "DIRECT_RETURN"
REVERSE_RETURN = "REVERSE_RETURN"
UNDECIDED = "UNDECIDED"
INHERIT = "INHERIT"

RESOLVED_BASIS = {
    DIRECT_RETURN,
    REVERSE_RETURN,
}

VALID_BASIS = {
    DIRECT_RETURN,
    REVERSE_RETURN,
    UNDECIDED,
    INHERIT,
}


@dataclass(frozen=True)
class EffectiveReturnArrangementRowV1:
    scope: str
    label: str

    effective_basis: str
    source: str
    status: str

    leg_id: str = ""
    leg_label: str = ""

    subleg_id: str = ""
    subleg_label: str = ""

    parent_subleg_id: str = ""
    parent_subleg_label: str = ""

    explicit_basis: str = INHERIT
    inherited_basis: str = UNDECIDED


@dataclass(frozen=True)
class EffectiveReturnArrangementResolutionV1:
    schema: str
    system_basis: str
    complete: bool
    rows: tuple[EffectiveReturnArrangementRowV1, ...]
    status: str


def resolve_effective_return_arrangements_v1(
        project_state_or_topology: Any = None,
        *,
        topology: Any = None,
        intent: Any = None,
) -> EffectiveReturnArrangementResolutionV1:
    """
    Resolve effective return arrangement basis for Proportioning.

    Accepts either:
        resolve_effective_return_arrangements_v1(project_state)

    or:
        resolve_effective_return_arrangements_v1(
            topology=topology,
            intent=intent,
        )
    """
    project_state = project_state_or_topology

    if topology is None:
        topology = getattr(project_state, "hydronic_topology", None)

        if topology is None:
            topology = project_state_or_topology

    if intent is None:
        intent = getattr(
            project_state,
            "hydronic_return_arrangement_intent",
            None,
        )

    system_basis = _normalise_system_basis(
        _intent_value(
            intent,
            (
                "system_arrangement",
                "system_mode",
                "system_basis",
                "return_arrangement_basis",
            ),
            UNDECIDED,
        )
    )

    leg_arrangements = _intent_map(
        intent,
        (
            "leg_arrangements",
            "leg_modes",
            "leg_return_arrangements",
            "leg_return_modes",
        ),
    )
    subleg_arrangements = _intent_map(
        intent,
        (
            "subleg_arrangements",
            "subleg_modes",
            "subleg_return_arrangements",
            "subleg_return_modes",
        ),
    )

    rows: list[EffectiveReturnArrangementRowV1] = []

    rows.append(
        EffectiveReturnArrangementRowV1(
            scope="SYSTEM",
            label="System",
            effective_basis=system_basis,
            explicit_basis=system_basis,
            inherited_basis=UNDECIDED,
            source="system",
            status=_basis_status(system_basis),
        )
    )

    topology_legs = list(getattr(topology, "legs", ()) or ())

    subleg_basis_by_id: dict[str, str] = {}

    for leg in topology_legs:
        leg_id = str(getattr(leg, "leg_id", "") or "")
        leg_label = _display_leg_label(
            str(
                getattr(leg, "label", None)
                or getattr(leg, "name", None)
                or leg_id
                or "Leg"
            )
        )

        explicit_leg_basis = _normalise_override_basis(
            leg_arrangements.get(leg_id, INHERIT)
        )

        if explicit_leg_basis in RESOLVED_BASIS:
            leg_effective_basis = explicit_leg_basis
            leg_source = "leg override"
            leg_status = _basis_status(
                leg_effective_basis,
                prefix="Override",
            )
        else:
            leg_effective_basis = system_basis
            leg_source = "inherit system"
            leg_status = _basis_status(
                leg_effective_basis,
                prefix="Inherits system",
            )

        rows.append(
            EffectiveReturnArrangementRowV1(
                scope="LEG",
                label=leg_label,
                leg_id=leg_id,
                leg_label=leg_label,
                explicit_basis=explicit_leg_basis,
                inherited_basis=system_basis,
                effective_basis=leg_effective_basis,
                source=leg_source,
                status=leg_status,
            )
        )

        leg_sublegs = _ordered_sublegs(
            list(getattr(leg, "sublegs", ()) or ())
        )
        primary_subleg = _primary_subleg_for_display(leg_sublegs)

        primary_subleg_id = ""
        primary_subleg_label = ""

        if primary_subleg is not None:
            primary_subleg_id = str(
                getattr(primary_subleg, "subleg_id", "") or ""
            )
            primary_subleg_label = _display_subleg_label(
                str(
                    getattr(primary_subleg, "label", None)
                    or getattr(primary_subleg, "name", None)
                    or primary_subleg_id
                    or "Primary subleg"
                )
            )

        def add_subleg_tree(
                sublegs,
                *,
                parent_subleg_id: str = "",
                parent_subleg_label: str = "",
        ) -> None:
            for subleg in _ordered_sublegs(list(sublegs or ())):
                subleg_id = str(getattr(subleg, "subleg_id", "") or "")
                subleg_label = _display_subleg_label(
                    str(
                        getattr(subleg, "label", None)
                        or getattr(subleg, "name", None)
                        or subleg_id
                        or "Subleg"
                    )
                )

                role_label = _subleg_role_label(subleg)
                role_lower = role_label.lower()

                is_primary = (
                    "primary-subleg" in subleg_id
                    or (
                        "common" in role_lower
                        and "branch" not in role_lower
                    )
                )

                effective_parent_id = str(parent_subleg_id or "")
                effective_parent_label = str(parent_subleg_label or "")

                # Current v1 topology may hold branch sublegs as leg-level
                # siblings. For effective-basis inheritance, attach those
                # branches to the leg primary/common subleg if available.
                if (
                        not effective_parent_id
                        and not is_primary
                        and primary_subleg_id
                        and subleg_id != primary_subleg_id
                ):
                    effective_parent_id = primary_subleg_id
                    effective_parent_label = primary_subleg_label

                is_branch = bool(effective_parent_id)

                explicit_subleg_basis = _normalise_override_basis(
                    subleg_arrangements.get(subleg_id, INHERIT)
                )

                if is_branch:
                    inherited_basis = subleg_basis_by_id.get(
                        effective_parent_id,
                        leg_effective_basis,
                    )
                    inherit_source = "inherit parent subleg"
                    scope = "BRANCH_SUBLEG"
                else:
                    inherited_basis = leg_effective_basis
                    inherit_source = "inherit leg"
                    scope = "COMMON_SUBLEG"

                if explicit_subleg_basis in RESOLVED_BASIS:
                    subleg_effective_basis = explicit_subleg_basis
                    source = "subleg override"
                    status = _basis_status(
                        subleg_effective_basis,
                        prefix="Override",
                    )
                else:
                    subleg_effective_basis = inherited_basis
                    source = inherit_source
                    status = _basis_status(
                        subleg_effective_basis,
                        prefix=(
                            "Inherits parent"
                            if is_branch
                            else "Inherits leg"
                        ),
                    )

                subleg_basis_by_id[subleg_id] = subleg_effective_basis

                rows.append(
                    EffectiveReturnArrangementRowV1(
                        scope=scope,
                        label=subleg_label,
                        leg_id=leg_id,
                        leg_label=leg_label,
                        subleg_id=subleg_id,
                        subleg_label=subleg_label,
                        parent_subleg_id=effective_parent_id,
                        parent_subleg_label=effective_parent_label,
                        explicit_basis=explicit_subleg_basis,
                        inherited_basis=inherited_basis,
                        effective_basis=subleg_effective_basis,
                        source=source,
                        status=status,
                    )
                )

                child_sublegs = list(
                    getattr(subleg, "sublegs", ()) or ()
                )
                if child_sublegs:
                    add_subleg_tree(
                        child_sublegs,
                        parent_subleg_id=subleg_id,
                        parent_subleg_label=subleg_label,
                    )

        add_subleg_tree(leg_sublegs)

    complete = all(
        row.effective_basis in RESOLVED_BASIS
        for row in rows
    )

    return EffectiveReturnArrangementResolutionV1(
        schema="effective_return_arrangement_resolution_v1",
        system_basis=system_basis,
        complete=complete,
        rows=tuple(rows),
        status=(
            "Effective return arrangement basis resolved"
            if complete
            else "Incomplete — unresolved return arrangement basis"
        ),
    )


def _intent_value(
        intent: Any,
        names: tuple[str, ...],
        default: Any,
) -> Any:
    if intent is None:
        return default

    if isinstance(intent, dict):
        for name in names:
            if name in intent:
                return intent.get(name)

        return default

    for name in names:
        if hasattr(intent, name):
            return getattr(intent, name)

    return default


def _intent_map(
        intent: Any,
        names: tuple[str, ...],
) -> dict[str, str]:
    value = _intent_value(intent, names, {})

    return {
        str(key): _normalise_override_basis(value)
        for key, value in dict(value or {}).items()
    }


def _normalise_system_basis(value: Any) -> str:
    basis = str(value or "").strip().upper()

    if basis in {
            DIRECT_RETURN,
            REVERSE_RETURN,
    }:
        return basis

    return UNDECIDED


def _normalise_override_basis(value: Any) -> str:
    basis = str(value or "").strip().upper()

    if basis in VALID_BASIS:
        return basis

    return INHERIT


def _basis_status(
        basis: str,
        *,
        prefix: str = "Basis",
) -> str:
    if basis == DIRECT_RETURN:
        return f"{prefix}: F&R / Direct return"

    if basis == REVERSE_RETURN:
        return f"{prefix}: F+RR / Reverse return"

    return f"{prefix}: unresolved"


def _ordered_sublegs(sublegs: list[Any]) -> list[Any]:
    """
    Common/primary sublegs first, then branches.

    This ensures sibling branch sublegs can inherit from the primary/common
    subleg when current topology does not yet model the take-off parent
    explicitly.
    """
    return sorted(
        list(sublegs or []),
        key=lambda subleg: (
            0 if _is_primary_or_common_subleg(subleg) else 1,
            str(getattr(subleg, "subleg_id", "") or ""),
        ),
    )


def _primary_subleg_for_display(sublegs: list[Any]) -> Any | None:
    for subleg in sublegs:
        if _is_primary_or_common_subleg(subleg):
            return subleg

    return sublegs[0] if sublegs else None


def _is_primary_or_common_subleg(subleg: Any) -> bool:
    subleg_id = str(getattr(subleg, "subleg_id", "") or "").lower()
    label = str(
        getattr(subleg, "label", None)
        or getattr(subleg, "name", None)
        or ""
    ).lower()

    source = f"{subleg_id} {label}"

    return (
        "primary-subleg" in source
        or (
            "common" in source
            and "branch" not in source
        )
    )


def _subleg_role_label(subleg: Any) -> str:
    subleg_id = str(getattr(subleg, "subleg_id", "") or "").lower()
    label = str(
        getattr(subleg, "label", None)
        or getattr(subleg, "name", None)
        or ""
    ).lower()

    source = f"{subleg_id} {label}"

    if "primary" in source or (
            "common" in source
            and "branch" not in source
    ):
        return "Common"

    if "branch" in source or "subleg-b" in source:
        return "Branch"

    return "Subleg"


def _display_leg_label(label: str) -> str:
    text = str(label or "")

    replacements = {
        "Heating Leg 1": "Leg 1",
        "Heating Leg 2": "Leg 2",
        "Heating Leg 3": "Leg 3",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text or "Leg"


def _display_subleg_label(label: str) -> str:
    text = str(label or "")

    replacements = {
        "Leg 1A Common subleg": "Subleg 1A",
        "Leg 1B Branch subleg": "Subleg 1B",
        "Leg 2A Common subleg": "Subleg 2A",
        "Leg 2B Branch subleg": "Subleg 2B",
        "Leg 3A Common subleg": "Subleg 3A",
        "Leg 3B Branch subleg": "Subleg 3B",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text or "Subleg"
