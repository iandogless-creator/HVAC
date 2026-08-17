# ======================================================================
# HVAC/heatloss/resolution/effective_snapshot_builder.py
# ======================================================================

from __future__ import annotations

from HVAC.core.value_resolution import (
    resolve_effective_height_m,
    resolve_effective_ach,
)

from HVAC.heatloss.dto.effective_room_snapshot import (
    EffectiveRoomSnapshotDTO,
)

from HVAC.heatloss.dto.effective_project_snapshot import (
    EffectiveProjectSnapshotDTO,
)

from HVAC.heatloss.dto.fabric_inputs import (
    FabricSurfaceInputDTO,
)

from HVAC.project.project_state import ProjectState
from HVAC.core.room_state import RoomStateV1
from HVAC.heatloss.fabric.room_fabric_rows_with_openings_v1 import (
    build_room_fabric_rows_with_openings_v1,
)

# ----------------------------------------------------------------------
# Room Snapshot (primitive)
# ----------------------------------------------------------------------
def build_effective_room_snapshot(
    project: ProjectState,
    room: RoomStateV1,
    *,
    internal_design_temp_C: float,
) -> EffectiveRoomSnapshotDTO:

    height_m, _ = resolve_effective_height_m(project, room)
    if height_m is None or float(height_m) <= 0.0:
        raise RuntimeError(
            f"Room '{room.room_id}' has no effective height"
        )

    ach, _ = resolve_effective_ach(project, room)
    if ach is None or float(ach) <= 0.0:
        raise RuntimeError(
            f"Room '{room.room_id}' has no effective ACH"
        )

    area_attr = getattr(room.space, "floor_area_m2", None)

    area = (
        float(area_attr())
        if callable(area_attr)
        else float(area_attr or 0.0)
    )

    volume = area * float(height_m)

    return EffectiveRoomSnapshotDTO(
        room_id=room.room_id,
        floor_area_m2=area,
        height_m=float(height_m),
        volume_m3=float(volume),
        ach=float(ach),
        internal_design_temp_C=float(internal_design_temp_C),
    )


# ======================================================================
# Construction U-value resolution
# ======================================================================

def _resolve_construction_u_value(
    project: ProjectState,
    construction_id: str,
) -> float | None:
    """
    Resolve construction U-value from current ProjectState authority.

    Current authority:
        project.constructions

    Legacy compatibility:
        project.construction_library
    """
    if not construction_id:
        return None

    cid = str(construction_id)

    constructions = getattr(project, "constructions", None)
    if constructions is None:
        constructions = getattr(project, "construction_library", None)

    if not constructions:
        return None

    construction = constructions.get(cid)
    if construction is None:
        return None

    value = (
        getattr(construction, "u_value_W_m2K", None)
        or getattr(construction, "u_value", None)
        or getattr(construction, "U", None)
    )

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None

# ----------------------------------------------------------------------
# Project Snapshot (composite)
# ----------------------------------------------------------------------
def build_effective_project_snapshot(
    project: ProjectState,
    *,
    internal_design_temp_C: float,
) -> EffectiveProjectSnapshotDTO:

    env = project.environment
    if env is None or env.external_design_temp_C is None:
        raise RuntimeError("External design temperature not defined")

    te_C = env.external_design_temp_C
    use_environmental_temperature = (
        getattr(env, "use_internal_environmental_temperature", False) is True
    )
    if use_environmental_temperature:
        if env.default_internal_temp_C is None:
            raise RuntimeError(
                "Internal environmental temperature (tei) not defined"
            )
        resolved_internal_temp_C = float(env.default_internal_temp_C)
    else:
        resolved_internal_temp_C = float(internal_design_temp_C)

    delta_t = resolved_internal_temp_C - te_C

    if delta_t <= 0:
        raise RuntimeError("Invalid ΔT")

    # --------------------------------------------------
    # Fabric surfaces (from topology → segments)
    # --------------------------------------------------

    surface_inputs: list[FabricSurfaceInputDTO] = []

    for room in project.rooms.values():

        rows = build_room_fabric_rows_with_openings_v1(project, room)

        if not rows:
            raise RuntimeError(
                f"Room '{room.room_id}' has no fabric surfaces"
            )

        for row in rows:

            area = row.area_m2
            if area is None or float(area) <= 0.0:
                raise RuntimeError(
                    f"Room '{room.room_id}' element '{row.element}' has invalid area"
                )

            construction_id = row.construction_id
            if not construction_id:
                raise RuntimeError(
                    f"Room '{room.room_id}' element '{row.element}' has no construction_id"
                )

            u_value = _resolve_construction_u_value(
                project,
                construction_id,
            )

            if u_value is None or float(u_value) <= 0.0:
                raise RuntimeError(
                    f"Construction '{construction_id}' has no valid U-value"
                )

            surface_inputs.append(
                FabricSurfaceInputDTO(
                    surface_id=str(row.surface_id),
                    room_id=str(room.room_id),
                    surface_class=str(row.element),
                    area_m2=float(area),
                    u_value_W_m2K=float(u_value),
                    delta_t_K=float(delta_t),
                )
            )

    if not surface_inputs:
        raise RuntimeError("No fabric surfaces generated")

    # --------------------------------------------------
    # Room snapshots
    # --------------------------------------------------

    room_snapshots = [
        build_effective_room_snapshot(
            project,
            room,
            internal_design_temp_C=resolved_internal_temp_C,
        )
        for room in project.rooms.values()
    ]

    return EffectiveProjectSnapshotDTO(
        project_id=project.project_id,
        external_design_temp_C=float(te_C),
        internal_design_temp_C=float(resolved_internal_temp_C),
        fabric_surfaces=surface_inputs,
        rooms=room_snapshots,
        use_internal_environmental_temperature=(
            use_environmental_temperature
        ),
    )
