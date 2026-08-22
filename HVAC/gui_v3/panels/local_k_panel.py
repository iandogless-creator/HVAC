# ======================================================================
# HVAC/gui_v3/panels/local_k_panel.py
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
)
from HVAC.hydronics.local_losses.local_k_intent_v1 import (
    LocalKIntentV1,
    LocalKSectionIntentV1,
)


class LocalKPanel(QWidget):
    """
    GUI v3 — Local K / Fittings Panel

    H-S12-A shell.

    Role
    ----
    Section-focused local-loss editor/preview.

    Authority
    ---------
    • Emits user intent only
    • Does not mutate ProjectState directly
    • Does not perform final proportioning
    • Does not balance
    • Does not select pumps
    """

    section_changed = Signal(str)
    local_k_changed = Signal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._is_priming = False
        self._current_velocity_m_s: float = 0.0
        self._current_dp_per_m: float = 0.0
        self._section_values: dict[str, dict] = {}
        self._current_section_id: str = ""

        root = QVBoxLayout(self)

        title = QLabel("Local K / Fittings")
        title.setStyleSheet("font-weight:600; padding:6px;")
        root.addWidget(title)

        # --------------------------------------------------
        # Section selection
        # --------------------------------------------------
        section_box = QGroupBox("Hydronic section")
        section_layout = QFormLayout(section_box)

        self._section_combo = QComboBox()
        # H-S69-B2 — keep route identity readable without allowing the
        # selector to consume the full width of a large workspace dock.
        self._section_combo.setMinimumWidth(420)
        self._section_combo.setMaximumWidth(720)
        self._section_combo.setToolTip(
            "Choose the stable Basic PS section.\n"
            "Fitting counts and straight length are stored per section."
        )
        section_layout.addRow("Section:", self._section_combo)

        self._pipe_label = QLabel("—")
        self._flow_label = QLabel("—")
        self._velocity_label = QLabel("—")
        self._dp_per_m_label = QLabel("—")

        section_layout.addRow("Pipe:", self._pipe_label)
        section_layout.addRow("Flow:", self._flow_label)
        section_layout.addRow("Velocity:", self._velocity_label)
        section_layout.addRow("Straight Δp/m:", self._dp_per_m_label)

        root.addWidget(section_box)

        # --------------------------------------------------
        # Local K counts
        # --------------------------------------------------
        fittings_box = QGroupBox("Local fittings — selected section")
        fittings_box.setToolTip(
            "Counts apply only to the selected section.\n"
            "They remain preliminary Local K intent."
        )
        fittings_layout = QFormLayout(fittings_box)

        self._bend_90 = self._make_count_spin()
        self._bend_45 = self._make_count_spin()
        self._tee_through = self._make_count_spin()
        self._tee_branch = self._make_count_spin()
        self._isolation_valve = self._make_count_spin()
        self._trv = self._make_count_spin()
        self._lockshield = self._make_count_spin()

        self._misc_k = QDoubleSpinBox()
        self._misc_k.setRange(0.0, 999.0)
        self._misc_k.setDecimals(2)
        self._misc_k.setSingleStep(0.1)
        self._misc_k.setMaximumWidth(120)
        self._misc_k.setToolTip(
            "Additional dimensionless K allowance.\n"
            "Use only for fittings not listed above."
        )

        fittings_layout.addRow("90° bends:", self._bend_90)
        fittings_layout.addRow("45° bends:", self._bend_45)
        fittings_layout.addRow("Tee through:", self._tee_through)
        fittings_layout.addRow("Tee branch:", self._tee_branch)
        fittings_layout.addRow("Isolation valves:", self._isolation_valve)
        fittings_layout.addRow("TRV:", self._trv)
        fittings_layout.addRow("Lockshield:", self._lockshield)
        fittings_layout.addRow("Misc K allowance:", self._misc_k)

        root.addWidget(fittings_box)

        # --------------------------------------------------
        # Length / preview
        # --------------------------------------------------
        preview_box = QGroupBox("Pressure-drop preview")
        preview_box.setToolTip(
            "Combines straight and local pressure-drop evidence.\n"
            "This is not final proportioning or pump duty."
        )
        preview_layout = QFormLayout(preview_box)

        self._length_m = QDoubleSpinBox()
        self._length_m.setRange(0.0, 10000.0)
        self._length_m.setDecimals(2)
        self._length_m.setSuffix(" m")
        self._length_m.setMaximumWidth(130)
        self._length_m.setToolTip(
            "Straight length for the selected section.\n"
            "Used with the displayed straight Δp/m in this preview."
        )
        self._straight_dp_label = QLabel("0.0 Pa")
        self._section_total_dp_label = QLabel("0.0 Pa")

        self._k_total_label = QLabel("0.00")
        self._local_dp_label = QLabel("0.0 Pa")
        self._status_label = QLabel("Local K intent — persisted per section")

        preview_layout.addRow("Straight length:", self._length_m)
        preview_layout.addRow("K total:", self._k_total_label)
        preview_layout.addRow("Local Δp:", self._local_dp_label)
        preview_layout.addRow("Straight Δp:", self._straight_dp_label)
        preview_layout.addRow("Section total Δp:", self._section_total_dp_label)
        preview_layout.addRow("Status:", self._status_label)

        root.addWidget(preview_box)
        root.addStretch(1)

        self._section_combo.currentIndexChanged.connect(
            self._on_section_changed
        )

        for spin in (
            self._bend_90,
            self._bend_45,
            self._tee_through,
            self._tee_branch,
            self._isolation_valve,
            self._trv,
            self._lockshield,
        ):
            spin.valueChanged.connect(self._emit_local_k_changed)

        self._misc_k.valueChanged.connect(self._emit_local_k_changed)
        self._length_m.valueChanged.connect(self._emit_local_k_changed)

    def set_sections(
        self,
        rows: list[dict],
        *,
        selected_section_id: str | None = None,
    ) -> None:
        self._is_priming = True
        self._section_combo.clear()

        for row in rows:
            scope = str(row.get("scope") or "").strip()
            scope_prefix = f"{scope} | " if scope else ""
            label = (
                f"{scope_prefix}{row.get('order', '—')} — "
                f"{row.get('from', '—')} → {row.get('to', '—')}"
            )
            self._section_combo.addItem(label, row)

        if selected_section_id:
            for index in range(self._section_combo.count()):
                row = self._section_combo.itemData(index) or {}
                if row.get("section_id") == selected_section_id:
                    self._section_combo.setCurrentIndex(index)
                    break

        self._load_current_section(emit=False)
        self._is_priming = False

    def set_section_values(
            self,
            section_values: dict[str, dict],
    ) -> None:
        """
        Replace runtime section values with persisted values from ProjectState.
        """
        self._section_values = dict(section_values or {})

        was_priming = self._is_priming
        self._is_priming = True
        self._load_current_section(emit=False)
        self._is_priming = was_priming

    def _current_section_payload(self) -> dict:
        return {
            "bend_90_count": self._bend_90.value(),
            "bend_45_count": self._bend_45.value(),
            "tee_through_count": self._tee_through.value(),
            "tee_branch_count": self._tee_branch.value(),
            "isolation_valve_count": self._isolation_valve.value(),
            "trv_count": self._trv.value(),
            "lockshield_count": self._lockshield.value(),
            "misc_k": self._misc_k.value(),
            "length_m": self._length_m.value(),
        }

    def _save_current_section_values(self) -> None:
        if not self._current_section_id:
            return

        self._section_values[self._current_section_id] = (
            self._current_section_payload()
        )

    def _load_section_values(self, section_id: str) -> None:
        values = self._section_values.get(section_id, {})

        self._is_priming = True

        self._bend_90.setValue(int(values.get("bend_90_count", 0)))
        self._bend_45.setValue(int(values.get("bend_45_count", 0)))
        self._tee_through.setValue(int(values.get("tee_through_count", 0)))
        self._tee_branch.setValue(int(values.get("tee_branch_count", 0)))
        self._isolation_valve.setValue(
            int(values.get("isolation_valve_count", 0))
        )
        self._trv.setValue(int(values.get("trv_count", 0)))
        self._lockshield.setValue(int(values.get("lockshield_count", 0)))
        self._misc_k.setValue(float(values.get("misc_k", 0.0)))
        self._length_m.setValue(float(values.get("length_m", 0.0)))

        self._is_priming = False

    def _make_count_spin(self) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(0, 99)
        spin.setMaximumWidth(90)
        spin.setToolTip(
            "Count on the selected section.\n"
            "The value is stored as Local K intent."
        )
        return spin

    def _on_section_changed(self) -> None:
        if self._is_priming:
            return

        # Save the values for the section we are leaving.
        self._save_current_section_values()

        row = self._section_combo.currentData() or {}
        section_id = str(row.get("section_id") or "")

        # Now move to the newly selected section.
        self._current_section_id = section_id

        self._load_current_section_basis(row)
        self._load_section_values(section_id)
        self._emit_local_k_changed()

        if section_id:
            self.section_changed.emit(section_id)

    def _load_current_section(self, *, emit: bool = True) -> None:
        row = self._section_combo.currentData() or {}
        section_id = str(row.get("section_id") or "")

        self._current_section_id = section_id
        self._load_current_section_basis(row)
        self._load_section_values(section_id)

        if emit and not self._is_priming:
            self._emit_local_k_changed()

    def _load_current_section_basis(self, row: dict) -> None:
        self._pipe_label.setText(str(row.get("pipe", "—")))
        self._flow_label.setText(str(row.get("flow", "—")))
        self._velocity_label.setText(str(row.get("velocity", "—")))
        self._dp_per_m_label.setText(str(row.get("dp_per_m", "—")))

        try:
            self._current_velocity_m_s = float(
                row.get("velocity_raw_m_s") or 0.0
            )
        except (TypeError, ValueError):
            self._current_velocity_m_s = 0.0

        try:
            self._current_dp_per_m = float(
                row.get("dp_per_m_raw") or 0.0
            )
        except (TypeError, ValueError):
            self._current_dp_per_m = 0.0

    def _current_k_total(self) -> float:
        # H-S12-A default K values. Preview only.
        return (
            self._bend_90.value() * 0.7
            + self._bend_45.value() * 0.4
            + self._tee_through.value() * 0.6
            + self._tee_branch.value() * 1.8
            + self._isolation_valve.value() * 0.2
            + self._trv.value() * 0.0
            + self._lockshield.value() * 0.0
            + self._misc_k.value()
        )

    def _emit_local_k_changed(self) -> None:
        if self._is_priming:
            return
        self._save_current_section_values()
        row = self._section_combo.currentData() or {}
        section_id = str(row.get("section_id") or "")

        water_density_kg_m3 = 998.0

        k_total = self._current_k_total()

        local_dp = (
                k_total
                * water_density_kg_m3
                * self._current_velocity_m_s ** 2
                / 2.0
        )

        length_m = float(self._length_m.value())
        straight_dp = self._current_dp_per_m * length_m
        section_total_dp = straight_dp + local_dp

        self._k_total_label.setText(f"{k_total:.2f}")
        self._local_dp_label.setText(f"{local_dp:.1f} Pa")
        self._straight_dp_label.setText(f"{straight_dp:.1f} Pa")
        self._section_total_dp_label.setText(f"{section_total_dp:.1f} Pa")

        self.local_k_changed.emit(
            {
                "section_id": section_id,
                "bend_90_count": self._bend_90.value(),
                "bend_45_count": self._bend_45.value(),
                "tee_through_count": self._tee_through.value(),
                "tee_branch_count": self._tee_branch.value(),
                "isolation_valve_count": self._isolation_valve.value(),
                "trv_count": self._trv.value(),
                "lockshield_count": self._lockshield.value(),
                "misc_k": self._misc_k.value(),
                "length_m": self._length_m.value(),
                "k_total": k_total,
                "local_pressure_drop_Pa": local_dp,
                "straight_pressure_drop_Pa": straight_dp,
                "section_total_pressure_drop_Pa": section_total_dp,
            }
        )