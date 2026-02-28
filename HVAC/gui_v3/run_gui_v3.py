# ======================================================================
# HVACgooee — GUI v3 Runner (DEV BOOTSTRAP)
# Phase II-B — Readiness → Execution wiring bring-up
# Status: DEV ONLY — NO PERSISTENCE
#
# Timestamp: Thursday 27 February 2026, 20:00 pm (UK)
# ======================================================================

from __future__ import annotations
import inspect
import sys
from typing import Iterable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.main_window import MainWindowV3

from HVAC.project.project_state import ProjectState
from HVAC.core.room_state import RoomStateV1

# ----------------------------------------------------------------------
# DEV: geometry class name drift tolerance
# ----------------------------------------------------------------------
from HVAC.core.room_state import RoomStateV1
from HVAC.geometry.space import Space
from HVAC.core.environment_state import EnvironmentStateV1

from HVAC.constructions.construction_preset import SurfaceClass  # your canonical enum

from HVAC.spaces.surface_engine_v1 import Surface
from HVAC.heatloss.fabric.resolved_fabric_surface import ResolvedFabricSurface


# ----------------------------------------------------------------------
# DEV: Surface constructor adapter (signature-tolerant)
# ----------------------------------------------------------------------
def _make_surface(
    *,
    surface_id: str,
    room_id: str,
    surface_class: SurfaceClass,
    area_m2: float,
    height_m: float,
) -> Surface:
    """
    Create a Surface even if its constructor signature evolves.

    We intentionally:
    - introspect Surface(...) parameters
    - map known semantic fields to whatever names exist
    - hard-fail if required params are missing
    """
    sig = inspect.signature(Surface)
    params = list(sig.parameters.values())

    # dataclass constructors never include "self", but we tolerate it anyway
    if params and params[0].name == "self":
        params = params[1:]

    if height_m <= 0:
        raise RuntimeError("DEV bootstrap: height_m must be > 0")

    # Derived
    length_m = area_m2 / height_m if height_m else 0.0

    # Semantic value map (expand only when Surface truly changes)
    # NOTE: we always try to supply BOTH identity and label if supported.
    value_by_name = {
        # identity / naming
        "surface_id": surface_id,
        "id": surface_id,
        "name": surface_id,  # safe fallback label

        # linkage
        "room_id": room_id,

        # classification (your codebase sometimes uses these names)
        "surface_class": surface_class,
        "surface_type": surface_class,
        "type": surface_class,

        # geometry
        "area_m2": float(area_m2),
        "length_m": float(length_m),
        "height_m": float(height_m),

        # orientation (optional)
        "orientation_deg": None,
    }

    args = []
    missing: list[str] = []

    for p in params:
        if p.name in value_by_name:
            args.append(value_by_name[p.name])
        elif p.default is inspect._empty:
            missing.append(p.name)

    if missing:
        raise RuntimeError(
            f"Surface signature changed: missing required params {missing}\n"
            f"{sig}"
        )

    return Surface(*args)

def _make_space(*, L: float, W: float, H: float) -> Space:
    """
    DEV: Construct Space in a signature-tolerant way.

    Space field names have drifted (length_m not accepted in this repo).
    This helper adapts to whatever Space.__init__ currently exposes.
    """
    sig = inspect.signature(Space)
    params = [p for p in sig.parameters.values() if p.name != "self"]
    names = [p.name for p in params]

    # 1) Try common keyword name sets (filtered to actual signature)
    candidate_maps = [
        {"length_m": L, "width_m": W, "height_m": H},
        {"length": L, "width": W, "height": H},
        {"L": L, "W": W, "H": H},
        {"L_m": L, "W_m": W, "H_m": H},
        {"l_m": L, "w_m": W, "h_m": H},
        {"x_m": L, "y_m": W, "z_m": H},
        {"x": L, "y": W, "z": H},
    ]

    for m in candidate_maps:
        kw = {k: v for k, v in m.items() if k in names}
        if not kw:
            continue
        try:
            return Space(**kw)
        except TypeError:
            pass

    # 2) Try positional if it looks like a 3-float ctor
    try:
        if len(params) >= 3:
            return Space(L, W, H)
    except TypeError:
        pass

    # 3) Last resort: attempt no-arg (if defaults exist)
    try:
        return Space()
    except TypeError as e:
        raise TypeError(
            "Cannot construct Space in DEV runner. "
            "Open HVAC/geometry/space.py and check Space.__init__ parameter names."
        ) from e
# ----------------------------------------------------------------------
# DEV: seed resolved fabric surfaces onto a room
# ----------------------------------------------------------------------
def _seed_resolved_fabric_surfaces(
    *,
    project: ProjectState,
    room_id: str,
    surfaces: Iterable[ResolvedFabricSurface],
) -> None:
    """
    DEV ONLY — attach resolved surfaces to the room.

    Rules:
    - do not create rooms here
    - do not mutate other structures
    """
    if room_id not in project.rooms:
        raise RuntimeError(f"DEV seed: room '{room_id}' not found in project.rooms")

    room = project.rooms[room_id]
    if not hasattr(room, "fabric_surfaces"):
        raise RuntimeError("RoomStateV1 missing fabric_surfaces list")

    room.fabric_surfaces.extend(list(surfaces))


# ----------------------------------------------------------------------
# DEV: make a minimal but valid ProjectState
# ----------------------------------------------------------------------

def make_dev_bootstrap_project_state() -> ProjectState:
    project = ProjectState(
        project_id="DEV-PROJ-001",
        name="DEV Bootstrap Project",
    )

    # 1) One room (minimal Space intent)

    room_id = "room-001"

    space = _make_space(L=3.0, W=4.0, H=2.4)

    room = RoomStateV1(
        room_id=room_id,
        name="Kitchen (DEV)",
        space=space,
    )

    project.rooms[room_id] = room

    # 2) Environment (Te present)
    project.environment = EnvironmentStateV1(
        external_design_temperature=-3.0,
        reference_delta_t=21.0,
    )

    # 3) Three resolved fabric surfaces (valid U)
    surfaces = [
        # External wall
        _make_surface(
            surface_id="surf-wall-001",
            room_id=room_id,
            surface_class=SurfaceClass.EXTERNAL_WALL,
            area_m2=12.0,
            height_m=2.4,
        ),
        # Window
        _make_surface(
            surface_id="surf-win-001",
            room_id=room_id,
            surface_class=SurfaceClass.WINDOW,  # or whatever your enum uses
            area_m2=3.0,
            height_m=1.2,
        ),
        # Roof / ceiling
        _make_surface(
            surface_id="surf-roof-001",
            room_id=room_id,
            surface_class=SurfaceClass.ROOF,  # or CEILING/ROOF_CEILING per your enum
            area_m2=10.0,
            height_m=2.4,
        ),
    ]

    resolved_list = [
        ResolvedFabricSurface(
            surface=surfaces[0],
            room_id=room_id,
            u_value_W_m2K=0.35,
            y_value_W_m2K=0.0,
            construction_id="DEV-WALL",
            notes="DEV wall",
        ),
        ResolvedFabricSurface(
            surface=surfaces[1],
            room_id=room_id,
            u_value_W_m2K=2.0,
            y_value_W_m2K=0.0,
            construction_id="DEV-WINDOW",
            notes="DEV window",
        ),
        ResolvedFabricSurface(
            surface=surfaces[2],
            room_id=room_id,
            u_value_W_m2K=0.20,
            y_value_W_m2K=0.0,
            construction_id="DEV-ROOF",
            notes="DEV roof",
        ),
    ]

    _seed_resolved_fabric_surfaces(
        project=project,
        room_id=room_id,
        surfaces=resolved_list,
    )

    # 4) Hard assertions (fail fast)
    assert project.environment is not None
    assert project.environment.external_design_temperature is not None

    assert project.rooms, "DEV bootstrap: project.rooms is empty"
    seeded = list(project.iter_fabric_surfaces())
    assert seeded, "DEV bootstrap: no fabric surfaces visible via iter_fabric_surfaces()"
    assert all(getattr(s, "u_value_W_m2K", 0.0) > 0.0 for s in seeded)
    return project


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> None:
    app = QApplication(sys.argv)

    project_state = make_dev_bootstrap_project_state()
    context = GuiProjectContext(project_state=project_state)

    win = MainWindowV3(context=context)
    win.show()

    # Phase II-B: auto-select first room so HLP isn't stuck on "No room selected"
    def _select_first_room() -> None:
        ps = getattr(context, "project_state", None)
        if ps is None or not ps.rooms:
            return
        first_room_id = next(iter(ps.rooms.keys()))
        if hasattr(context, "set_current_room"):
            context.set_current_room(first_room_id)
        elif hasattr(context, "set_current_room_id"):
            context.set_current_room_id(first_room_id)
        else:
            # As a last resort: set attribute directly (DEV only)
            setattr(context, "current_room_id", first_room_id)
            if hasattr(context, "current_room_changed"):
                context.current_room_changed.emit(first_room_id)

    QTimer.singleShot(0, _select_first_room)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()