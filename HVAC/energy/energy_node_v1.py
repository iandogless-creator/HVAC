from dataclasses import dataclass, field
from typing import Optional, List


@dataclass(slots=True)
class PlantItem:
    """
    Internal plant component.
    Purely descriptive at v1.
    """
    item_type: str          # boiler | heat_pump | pump | vessel | header
    capacity_w: Optional[float] = None
    notes: Optional[str] = None


@dataclass(slots=True)
class EnergyNode:
    """
    Energy node / plant room (v1).

    Represents anything from:
    - cupboard boiler
    - plant room
    - energy centre building
    """

    node_id: str
    name: str

    # Internal heat losses (optional, can be treated as another 'room' later)
    internal_losses_w: float = 0.0

    # Plant inside this node
    plant_items: List[PlantItem] = field(default_factory=list)

    # Available to the network (declared, not solved yet)
    design_flow_available_lps: Optional[float] = None
    design_head_available_m: Optional[float] = None

cupboard_boiler = EnergyNode(
    node_id="EN_01",
    name="Kitchen cupboard boiler",
    internal_losses_w=150.0,
)

cupboard_boiler.plant_items.extend([
    PlantItem(item_type="boiler", capacity_w=24000),
    PlantItem(item_type="pump"),
    PlantItem(item_type="expansion_vessel"),
])

plant_room = EnergyNode(
    node_id="EN_PLANT",
    name="Main boiler house",
    internal_losses_w=2500.0,
)

plant_room.plant_items.extend([
    PlantItem(item_type="boiler", capacity_w=500_000),
    PlantItem(item_type="boiler", capacity_w=500_000),
    PlantItem(item_type="pump"),
    PlantItem(item_type="pump"),
    PlantItem(item_type="low_loss_header"),
])
