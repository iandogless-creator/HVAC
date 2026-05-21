# ======================================================================
# HVAC/hydronics/topology/leg_subleg_dto_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ======================================================================
# Role constants
# ======================================================================

HYDRO_ROUTE_ROLE_COMMON_LEG = "COMMON_LEG"
HYDRO_ROUTE_ROLE_SUBLEG_CIRCUIT = "SUBLEG_CIRCUIT"
HYDRO_ROUTE_ROLE_TERMINAL_BRANCH = "TERMINAL_BRANCH"
HYDRO_ROUTE_ROLE_INTERMEDIATE_BRANCH = "INTERMEDIATE_BRANCH"

HYDRO_TERMINATION_EMITTER = "EMITTER"
HYDRO_TERMINATION_CONTINUES = "CONTINUES"
HYDRO_TERMINATION_UNRESOLVED = "UNRESOLVED"


# ======================================================================
# Display helper
# ======================================================================

def display_label(
    *,
    user_label: str = "",
    system_label: str = "",
    fallback_id: str = "",
) -> str:
    """
    Resolve display label for schematics/tables.

    Display rule:
    • use user label if provided
    • otherwise use generated system label
    • otherwise use stable internal ID
    """
    return user_label or system_label or fallback_id


# ======================================================================
# DTOs
# ======================================================================

@dataclass(frozen=True, slots=True)
class HydronicRouteNodeV1:
    """
    Read-only hydronic topology node.

    A node is a logical point in the hydronic route tree.
    It is not a CAD coordinate.

    User labels are display-only and do not replace node_id authority.
    """

    node_id: str

    system_label: str
    user_label: str = ""

    room_id: Optional[str] = None
    emitter_id: Optional[str] = None

    note: str = ""

    @property
    def label(self) -> str:
        return display_label(
            user_label=self.user_label,
            system_label=self.system_label,
            fallback_id=self.node_id,
        )


@dataclass(frozen=True, slots=True)
class HydronicRouteSectionV1:
    """
    Read-only hydronic route section.

    A section carries one flow value.

    Flow meaning depends on role:
    • COMMON_LEG carries ΣFr
    • SUBLEG_CIRCUIT carries AcFr
    • INTERMEDIATE_BRANCH carries AcFr
    • TERMINAL_BRANCH carries Fr

    This DTO does not calculate pressure loss or pipe size.
    """

    section_id: str

    system_label: str
    user_label: str = ""

    from_node_id: str = ""
    to_node_id: str = ""

    role: str = HYDRO_ROUTE_ROLE_SUBLEG_CIRCUIT

    parent_section_id: Optional[str] = None
    child_section_ids: tuple[str, ...] = tuple()

    flow_kg_s: Optional[float] = None
    flow_basis: str = ""

    pipe_diameter_mm: Optional[float] = None

    termination: str = HYDRO_TERMINATION_UNRESOLVED

    note: str = ""

    @property
    def label(self) -> str:
        return display_label(
            user_label=self.user_label,
            system_label=self.system_label,
            fallback_id=self.section_id,
        )


@dataclass(frozen=True, slots=True)
class HydronicTerminalCircuitV1:
    """
    Read-only terminal circuit descriptor.

    A terminal circuit is the complete hydraulic path from boiler/pump,
    through common leg/sublegs/terminal branch/emitter, and back.

    H-T1 does not calculate Δp.
    """

    circuit_id: str

    system_label: str
    user_label: str = ""

    terminal_node_id: str = ""
    emitter_id: Optional[str] = None

    section_ids: tuple[str, ...] = tuple()

    total_length_m: Optional[float] = None
    total_pressure_drop_Pa: Optional[float] = None

    is_selected_index_route: bool = False
    is_true_index_circuit: bool = False

    note: str = ""

    @property
    def label(self) -> str:
        return display_label(
            user_label=self.user_label,
            system_label=self.system_label,
            fallback_id=self.circuit_id,
        )


@dataclass(frozen=True, slots=True)
class HydronicLegSublegTopologyV1:
    """
    Read-only hydronic leg/subleg topology projection.

    H-T1 scope:
    • represent Leg 1 / common leg
    • represent subleg circuits
    • represent terminal/radiator branches
    • support user-facing labels
    • reserve one carried flow field per section
    • reserve terminal-circuit ranking fields

    Out of scope:
    • pressure-loss calculation
    • true index-circuit selection
    • pump selection
    • balancing valve setting
    • manufacturer radiator data
    """

    nodes: tuple[HydronicRouteNodeV1, ...]
    sections: tuple[HydronicRouteSectionV1, ...]
    terminal_circuits: tuple[HydronicTerminalCircuitV1, ...]

    common_leg_section_id: Optional[str] = None
    selected_index_route_circuit_id: Optional[str] = None
    true_index_circuit_id: Optional[str] = None

    basis: str = "H-T1 DTO skeleton only"