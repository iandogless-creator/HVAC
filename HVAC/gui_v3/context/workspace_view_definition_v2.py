from __future__ import annotations

from copy import deepcopy


WORKSPACE_PANEL_PLACEMENTS_V2 = frozenset({"main", "side", "bottom"})
WORKSPACE_PRESENTATION_MODES_V2 = frozenset({"main", "floating"})
MAX_WORKSPACE_VIEWS_V2 = 64
MAX_WORKSPACE_PANELS_V2 = 64
MAX_WORKSPACE_VIEW_NAME_LENGTH_V2 = 80
MAX_WORKSPACE_SIDE_PANELS_V2 = 2
MAX_WORKSPACE_BOTTOM_PANELS_V2 = 2


_DEFAULT_WORKSPACE_VIEW_ROWS_V2 = (
    (
        "heat_loss",
        "Heat Loss",
        (
            ("dock_heat_loss", "main"),
            ("dock_environment", "side"),
            ("dock_rooms", "side"),
            ("dock_geometry", "bottom"),
            ("dock_ach", "bottom"),
        ),
    ),
    (
        "building_edit",
        "Building Edit",
        (
            ("dock_uvp", "main"),
            ("dock_construction", "side"),
            ("dock_rooms", "side"),
            ("dock_geometry", "bottom"),
        ),
    ),
    (
        "openings",
        "Openings",
        (
            ("dock_uvp", "main"),
            ("dock_heat_loss", "side"),
            ("dock_rooms", "side"),
            ("dock_construction", "bottom"),
        ),
    ),
    (
        "hydronics_setup",
        "Hydronics Setup",
        (
            ("dock_topology_arranger", "main"),
            ("dock_environment", "side"),
            ("dock_hydronic_control", "side"),
            ("dock_rooms", "bottom"),
        ),
    ),
    (
        "basic_sizing",
        "Basic Sizing",
        (
            ("dock_basic_hydronics", "main"),
            ("dock_local_k", "side"),
            ("dock_rooms", "bottom"),
        ),
    ),
    (
        "proportioning",
        "Proportioning",
        (
            ("dock_hydronics", "main"),
            ("dock_local_k", "side"),
        ),
    ),
    (
        "results",
        "Proportioned Results",
        (
            ("dock_hydronics", "main"),
            ("dock_project", "side"),
            ("dock_rooms", "bottom"),
        ),
    ),
)


def default_workspace_views_v2() -> list[dict]:
    """Return the seven editable starting views as fresh JSON-safe values."""
    return [
        {
            "view_id": view_id,
            "name": name,
            "panels": dict(panel_rows),
        }
        for view_id, name, panel_rows in _DEFAULT_WORKSPACE_VIEW_ROWS_V2
    ]


def _bounded_identity_v2(value: object, *, maximum: int) -> str:
    identity = str(value or "").strip()
    if not identity or len(identity) > maximum:
        return ""
    if not all(character.isalnum() or character in "_-" for character in identity):
        return ""
    return identity


def _normalise_panels_v2(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}

    panels: dict[str, str] = {}
    main_panel_id = ""
    placement_counts = {"side": 0, "bottom": 0}
    for raw_panel_id, raw_placement in list(value.items())[:MAX_WORKSPACE_PANELS_V2]:
        panel_id = _bounded_identity_v2(raw_panel_id, maximum=128)
        placement = str(raw_placement or "").strip().lower()
        if not panel_id or placement not in WORKSPACE_PANEL_PLACEMENTS_V2:
            continue
        if placement == "main":
            if main_panel_id:
                placement = next((
                    candidate
                    for candidate, maximum in (
                        ("side", MAX_WORKSPACE_SIDE_PANELS_V2),
                        ("bottom", MAX_WORKSPACE_BOTTOM_PANELS_V2),
                    )
                    if placement_counts[candidate] < maximum
                ), "")
                if not placement:
                    continue
            else:
                main_panel_id = panel_id
        elif placement_counts[placement] >= (
                MAX_WORKSPACE_SIDE_PANELS_V2
                if placement == "side"
                else MAX_WORKSPACE_BOTTOM_PANELS_V2
        ):
            continue
        if placement != "main":
            placement_counts[placement] += 1
        panels[panel_id] = placement

    if panels and not main_panel_id:
        first_panel_id = next(iter(panels))
        panels[first_panel_id] = "main"
    return panels


def normalise_workspace_views_v2(
        value: object,
        *,
        fallback_to_defaults: bool = True,
) -> list[dict]:
    """Return bounded named views with one main panel in every view."""
    if not isinstance(value, (list, tuple)):
        return default_workspace_views_v2() if fallback_to_defaults else []

    views: list[dict] = []
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for raw_view in value[:MAX_WORKSPACE_VIEWS_V2]:
        if not isinstance(raw_view, dict):
            continue
        view_id = _bounded_identity_v2(raw_view.get("view_id"), maximum=64)
        name = str(raw_view.get("name") or "").strip()
        panels = _normalise_panels_v2(raw_view.get("panels"))
        folded_name = name.casefold()
        if (
            not view_id
            or view_id in seen_ids
            or not name
            or len(name) > MAX_WORKSPACE_VIEW_NAME_LENGTH_V2
            or folded_name in seen_names
            or not panels
        ):
            continue
        seen_ids.add(view_id)
        seen_names.add(folded_name)
        views.append({"view_id": view_id, "name": name, "panels": panels})

    if views:
        return views
    return default_workspace_views_v2() if fallback_to_defaults else []


def migrate_workspace_views_v1_to_v2(
        *,
        workspace_panel_sets_v1: object,
        named_workspace_layouts_v1: object,
) -> list[dict]:
    """Project legacy membership into editable views without Qt state blobs."""
    defaults = default_workspace_views_v2()
    docked_sets = (
        workspace_panel_sets_v1
        if isinstance(workspace_panel_sets_v1, dict)
        else {}
    )
    exploded_layouts = (
        named_workspace_layouts_v1
        if isinstance(named_workspace_layouts_v1, dict)
        else {}
    )

    migrated: list[dict] = []
    for default in defaults:
        view_id = default["view_id"]
        panel_ids = docked_sets.get(f"{view_id}:docked")
        if not isinstance(panel_ids, (list, tuple)) or not panel_ids:
            layout = exploded_layouts.get(f"{view_id}:exploded")
            panel_ids = layout.get("panel_ids") if isinstance(layout, dict) else None
        if isinstance(panel_ids, (list, tuple)) and panel_ids:
            default_placements = default["panels"]
            panels = {
                str(panel_id): default_placements.get(str(panel_id), "side")
                for panel_id in panel_ids
            }
            default = {**default, "panels": panels}
        migrated.append(default)

    user_layout = exploded_layouts.get("user:exploded")
    if isinstance(user_layout, dict):
        raw_docks = user_layout.get("docks")
        if isinstance(raw_docks, dict) and raw_docks:
            panels = {
                str(panel_id): "side"
                for panel_id in raw_docks
            }
            first_panel_id = next(iter(panels))
            panels[first_panel_id] = "main"
            migrated.append({
                "view_id": "user",
                "name": "User Workspace",
                "panels": panels,
            })

    return normalise_workspace_views_v2(migrated)


def normalise_last_workspace_view_v2(
        value: object,
        *,
        workspace_views: list[dict] | tuple[dict, ...],
) -> dict[str, str]:
    view_ids = {
        str(view.get("view_id") or "")
        for view in workspace_views
        if isinstance(view, dict)
    }
    if isinstance(value, dict):
        view_id = str(value.get("view_id") or "").strip()
        mode = str(value.get("mode") or "").strip().lower()
        if view_id in view_ids and mode in WORKSPACE_PRESENTATION_MODES_V2:
            return {"view_id": view_id, "mode": mode}

    first_view_id = next(iter(view_ids), "heat_loss")
    for view in workspace_views:
        if isinstance(view, dict) and view.get("view_id"):
            first_view_id = str(view["view_id"])
            break
    return {"view_id": first_view_id, "mode": "main"}


def copied_workspace_views_v2(value: list[dict]) -> tuple[dict, ...]:
    return tuple(deepcopy(value))
