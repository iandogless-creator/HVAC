# ======================================================================
# HVAC/gui_v3/adapters/construction_panel_adapter.py
# ======================================================================

from __future__ import annotations

from HVAC.gui_v3.panels.construction_panel import ConstructionPanel
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.wizards.construction_wizard import ConstructionWizard

class ConstructionPanelAdapter:
    """
    GUI v3 — Construction Panel Adapter

    Responsibilities
    ----------------
    • Observe construction focus from GuiProjectContext
    • Read ProjectState.constructions
    • Project selected construction into ConstructionPanel

    Forbidden
    ---------
    • No ProjectState mutation
    • No U-value calculation
    • No topology mutation
    """

    def __init__(
        self,
        *,
        panel: ConstructionPanel,
        context: GuiProjectContext,
    ) -> None:
        self._panel = panel
        self._context = context

        self._context.construction_focus_changed.connect(
            self._on_construction_focus_changed
        )

        self._panel.construction_assign_requested.connect(
            self._on_assign_requested
        )

        if hasattr(self._context, "surface_focus_changed"):
            self._context.surface_focus_changed.connect(self._on_surface_focus_changed)

        self.refresh()

    def _build_library(self) -> dict[str, dict[str, list[tuple[str, str]]]]:
        ps = self._context.project_state
        if ps is None:
            return {}

        library: dict[str, dict[str, list[tuple[str, str]]]] = {}

        for cid, construction in sorted(ps.constructions.items()):
            name = getattr(construction, "name", cid) or cid
            element, category = self._classify_construction(cid, name)

            library.setdefault(element, {}).setdefault(category, []).append(
                (cid, name)
            )

        return library

    @staticmethod
    def _classify_construction(cid: str, name: str) -> tuple[str, str]:
        text = f"{cid} {name}".upper()

        if "INT-WALL" in text or "INTERNAL WALL" in text:
            return "Wall", "Internal Wall"

        if "WALL" in text:
            return "Wall", "External Wall"

        if "ROOF" in text or "CEILING" in text:
            return "Roof / Ceiling", "Roof / Ceiling"

        if "FLOOR" in text:
            return "Floor", "Floor"

        if "WINDOW" in text or "DOOR" in text:
            return "Window / Door", "Window / Door"

        return "Other", "Other"

    def _on_surface_focus_changed(self, surface_id: str | None) -> None:
        if hasattr(self._panel, "set_selected_surface"):
            self._panel.set_selected_surface(surface_id)

    def _on_assign_requested(self, cid: str) -> None:
        ps = self._context.project_state
        if ps is None:
            return

        surface_id = getattr(self._context, "current_surface_id", None)

        if not surface_id:
            return

        ConstructionWizard.set_surface_construction(ps, surface_id, cid)
        ps.mark_heatloss_dirty()

        if hasattr(self._context, "set_current_construction_id"):
            self._context.set_current_construction_id(cid)

        self._context.notify_project_changed()
        self._on_construction_focus_changed(cid)

    def _on_construction_focus_changed(self, cid: str) -> None:
        ps = self._context.project_state
        if ps is None:
            return

        construction = ps.constructions.get(cid)
        if construction is None:
            self._panel.set_focused_construction(
                construction_id=cid,
                name=None,
                u_value_W_m2K=None,
                usage_count=0,
            )
            return
        self._panel.set_selected_construction_id(cid)
        mapping = getattr(ps, "surface_construction_map", {}) or {}

        usage_count = sum(
            1 for assigned_cid in mapping.values()
            if assigned_cid == cid
        )

        self._panel.set_focused_construction(
            construction_id=cid,
            name=construction.name,
            u_value_W_m2K=construction.u_value_W_m2K,
            usage_count=usage_count,
        )
        surface_id = getattr(self._context, "current_surface_id", None)
        if hasattr(self._panel, "set_selected_surface"):
            self._panel.set_selected_surface(surface_id)

    def refresh(self) -> None:
        self._panel.set_construction_library(self._build_library())

        cid = getattr(self._context, "current_construction_id", None)
        if cid:
            self._on_construction_focus_changed(cid)