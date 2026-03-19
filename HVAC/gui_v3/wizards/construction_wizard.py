from dataclasses import dataclass, field

@dataclass(slots=True)
class FabricElementV1:
    """
    Authoritative modelling intent for a fabric heat-loss element.

    Stored in RoomState.
    """

    element_class: str
    area_m2: float
    construction_id: str | None = None

room.fabric_elements = [

    FabricElementV1(
        element_class="external_wall",
        area_m2=7.71,
        construction_id="wall_cavity_insulated"
    ),

    FabricElementV1(
        element_class="window",
        area_m2=2.4,
        construction_id="double_glazing"
    ),

    FabricElementV1(
        element_class="door",
        area_m2=1.89,
        construction_id="timber_door"
    ),
]

project.mark_heatloss_dirty()