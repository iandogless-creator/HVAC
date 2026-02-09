from dataclasses import dataclass, field

from HVAC_legacy.hydronics.models.emitter_v1 import EmitterV1


@dataclass(slots=True)
class BoilerNodeV1:
    boiler_id: str
    name: str


@dataclass(slots=True)
class TerminalNodeV1:
    terminal_id: str
    room_name: str
    design_heat_loss_w: float


@dataclass(slots=True)
class HydronicSkeletonV1:
    """
    Declarative hydronic system intent.
    """

    skeleton_id: str
    boiler: BoilerNodeV1
    terminals: dict[str, TerminalNodeV1]

    # Intent only — no physics
    emitters: dict[str, EmitterV1] = field(default_factory=dict)
