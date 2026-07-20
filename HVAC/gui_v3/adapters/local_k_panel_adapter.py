# ======================================================================
# HVAC/gui_v3/adapters/local_k_panel_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.gui_v3.panels.local_k_panel import LocalKPanel
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.hydronics.local_losses.local_k_section_projection_v1 import (
    build_local_k_section_projection_v1,
)
from HVAC.hydronics.local_losses.local_k_intent_v1 import (
    LocalKIntentV1,
    LocalKSectionIntentV1,
)

class LocalKPanelAdapter:
    """
    GUI v3 — Local K / Fittings Panel Adapter

    H-S12-A shell.

    Role
    ----
    Reads Basic PS section basis and feeds the Local K panel.

    Authority
    ---------
    • Reads ProjectState
    • Does not mutate ProjectState yet
    • Does not persist Local K counts yet
    • Does not perform final proportioning
    • Does not balance
    • Does not select pumps
    """

    def __init__(
        self,
        *,
        panel: LocalKPanel,
        context: GuiProjectContext,
    ) -> None:
        self._panel = panel
        self._context = context
        self._selected_section_id: str | None = None

        self._panel.section_changed.connect(self._on_section_changed)
        self._panel.local_k_changed.connect(self._on_local_k_changed)

        self._subscribe_if_present("room_state_changed", self.refresh)
        self._subscribe_if_present("project_changed", self.refresh)

        self.refresh()

    def refresh(self, *args: Any, **kwargs: Any) -> None:
        project = self._context.project_state

        if project is None:
            self._panel.set_sections([])
            return

        persisted_values: dict[str, dict] = {}

        intent = getattr(project, "hydronic_local_k_intent", None)

        if intent is not None:
            for section_id, section in intent.sections.items():
                persisted_values[section_id] = section.to_dict()

        if getattr(project, "hydronic_topology", None) is None:
            self._panel.set_section_values(persisted_values)
            self._panel.set_sections([])
            return

        try:
            projection = build_local_k_section_projection_v1(
                project,
                leg_id="leg-001",
            )
        except Exception as exc:
            print("[LOCAL K SECTIONS ERROR]", repr(exc))
            self._panel.set_sections([])
            return



        rows: list[dict] = []

        for row in projection.rows:
            rows.append(
                {
                    "section_id": row.section_id,
                    "scope": row.section_scope,
                    "order": row.order,
                    "from": row.from_label,
                    "to": row.to_room_label,
                    "pipe": row.pipe_size_label,
                    "flow": f"{row.carried_flow_kg_s:.4f} kg/s",
                    "velocity": f"{row.velocity_m_s:.3f} m/s",
                    "velocity_raw_m_s": row.velocity_m_s,
                    "dp_per_m": f"{row.pressure_gradient_Pa_per_m:.1f} Δp/m",
                    "dp_per_m_raw": row.pressure_gradient_Pa_per_m,
                    "status": row.status,
                }
            )

        self._panel.set_section_values(persisted_values)

        self._panel.set_sections(
            rows,
            selected_section_id=self._selected_section_id,
        )

    def _on_section_changed(self, section_id: str) -> None:
        self._selected_section_id = str(section_id or "")

        if not self._selected_section_id:
            return

        signal = getattr(
            self._context,
            "hydronic_section_focus_requested",
            None,
        )

        emit = getattr(signal, "emit", None)

        if callable(emit):
            emit(self._selected_section_id)

    def _on_local_k_changed(self, payload: dict) -> None:
        """
        H-S12-B:
        Persist Local K / fittings intent per Basic PS section_id.
        """
        project = self._context.project_state

        if project is None:
            return

        section_id = str(payload.get("section_id") or "")

        if not section_id:
            return

        self._selected_section_id = section_id

        intent = getattr(project, "hydronic_local_k_intent", None)

        if intent is None:
            intent = LocalKIntentV1()
            project.hydronic_local_k_intent = intent

        raw_length_m = payload.get("length_m")

        intent.sections[section_id] = LocalKSectionIntentV1(
            section_id=section_id,
            bend_90_count=int(payload.get("bend_90_count") or 0),
            bend_45_count=int(payload.get("bend_45_count") or 0),
            tee_through_count=int(payload.get("tee_through_count") or 0),
            tee_branch_count=int(payload.get("tee_branch_count") or 0),
            isolation_valve_count=int(payload.get("isolation_valve_count") or 0),
            trv_count=int(payload.get("trv_count") or 0),
            lockshield_count=int(payload.get("lockshield_count") or 0),
            misc_k=float(payload.get("misc_k") or 0.0),
            length_m=(
                None
                if raw_length_m is None
                else float(raw_length_m)
            ),
        )

        project.hydronics_valid = False
        # H-S12-C:
        # Local K intent affects downstream hydronic preview displays.
        # Notify any panels/adapters observing project-level changes.
        for signal_name in (
            "project_state_changed",
            "project_changed",
            "room_state_changed",
        ):
            signal = getattr(self._context, signal_name, None)

            if signal is None:
                continue

            emit = getattr(signal, "emit", None)
            if callable(emit):
                try:
                    emit()
                except TypeError:
                    try:
                        emit(project)
                    except TypeError:
                        pass

    def _subscribe_if_present(self, signal_name: str, callback) -> None:
        signal = getattr(self._context, signal_name, None)

        if signal is None:
            return

        try:
            signal.connect(callback)
        except TypeError:
            try:
                signal.connect(lambda *args, **kwargs: callback())
            except TypeError:
                pass