from __future__ import annotations


PANEL_CATEGORY_BY_DOCK_ID_V1: dict[str, str] = {
    "dock_project": "main_readonly",
    "dock_rooms": "main_readonly",
    "dock_heat_loss": "main_readonly",
    "dock_education": "main_readonly",
    "dock_basic_hydronics": "main_readonly",
    "dock_hydronics": "main_readonly",
    "dock_environment": "helper_input",
    "dock_geometry": "helper_input",
    "dock_ach": "helper_input",
    "dock_construction": "helper_input",
    "dock_uvp": "helper_input",
    "dock_hydronic_control": "helper_input",
    "dock_topology_arranger": "helper_input",
    "dock_local_k": "helper_input",
    "dock_dev": "helper_input",
}


def panel_category_for_dock_id_v1(dock_id: object) -> str | None:
    stable_id = str(dock_id or "").strip()
    return PANEL_CATEGORY_BY_DOCK_ID_V1.get(stable_id)
