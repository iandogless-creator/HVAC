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

        self._panel.set_sections(
            rows,
            selected_section_id=self._selected_section_id,
        )

    def _on_section_changed(self, section_id: str) -> None:
        self._selected_section_id = str(section_id or "")

    def _on_local_k_changed(self, payload: dict) -> None:
        """
        H-S12-A:
        Runtime-only Local K preview.

        Persistence and schematic/proportioning propagation come later.
        """
        section_id = str(payload.get("section_id") or "")

        if section_id:
            self._selected_section_id = section_id

        # Intentionally not persisted yet.
        # Later H-S13 will write this payload into a ProjectState-owned
        # Local K intent/schedule.

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