# ======================================================================
# HVACgooee — GUI Settings (GUI v3)
# Phase: E/F — Workspace Persistence
# Status: CANONICAL
# ======================================================================
# NOTE: Appearance preference is GUI-only and outside ProjectState.
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json


NAMED_WORKSPACE_LAYOUT_SCHEMA_V1 = 1
WORKSPACE_VIEW_IDS_V1 = frozenset({
    "heat_loss",
    "building_edit",
    "openings",
    "hydronics_setup",
    "basic_sizing",
    "proportioning",
    "results",
})
WORKSPACE_VIEW_MODES_V1 = frozenset({"docked", "exploded"})
APPEARANCE_SCHEMES_V1 = frozenset({"light", "dark"})


def _normalise_appearance_scheme_v1(value: object) -> str:
    scheme = str(value or "").strip().lower()
    return scheme if scheme in APPEARANCE_SCHEMES_V1 else "light"


def _normalise_last_workspace_presentation_v1(
        value: object,
) -> dict[str, str] | None:
    """Return one bounded, recognised GUI workspace presentation."""
    if not isinstance(value, dict):
        return None
    view_id = str(value.get("view_id") or "").strip()
    mode = str(value.get("mode") or "").strip()
    if view_id not in WORKSPACE_VIEW_IDS_V1:
        return None
    if mode not in WORKSPACE_VIEW_MODES_V1:
        return None
    return {"view_id": view_id, "mode": mode}


def _normalise_named_workspace_layouts_v1(value: object) -> dict[str, dict]:
    """Return only bounded, JSON-safe floating-dock geometry evidence."""
    if not isinstance(value, dict):
        return {}

    layouts: dict[str, dict] = {}
    for raw_name, raw_layout in value.items():
        name = str(raw_name or "").strip()
        if not name or len(name) > 128 or not isinstance(raw_layout, dict):
            continue
        raw_docks = raw_layout.get("docks")
        if not isinstance(raw_docks, dict):
            continue

        docks: dict[str, dict] = {}
        for raw_dock_id, raw_geometry in raw_docks.items():
            dock_id = str(raw_dock_id or "").strip()
            if (
                not dock_id
                or len(dock_id) > 128
                or not isinstance(raw_geometry, dict)
            ):
                continue

            coordinates: dict[str, int] = {}
            valid = True
            for key, lower, upper in (
                ("x", -100000, 100000),
                ("y", -100000, 100000),
                ("width", 80, 20000),
                ("height", 80, 20000),
            ):
                raw_number = raw_geometry.get(key)
                if isinstance(raw_number, bool) or not isinstance(raw_number, int):
                    valid = False
                    break
                if raw_number < lower or raw_number > upper:
                    valid = False
                    break
                coordinates[key] = raw_number
            if not valid:
                continue

            screen_name = str(raw_geometry.get("screen_name") or "").strip()
            if len(screen_name) > 256:
                continue
            coordinates["screen_name"] = screen_name
            docks[dock_id] = coordinates

        if docks:
            layouts[name] = {
                "schema": NAMED_WORKSPACE_LAYOUT_SCHEMA_V1,
                "docks": docks,
            }
    return layouts


class GuiSettings:
    """
    GUI-only persistence container.

    Responsibilities
    ----------------
    • Store QMainWindow geometry & dock layout
    • Best-effort restore
    • No ProjectState knowledge
    • No panel knowledge
    • Store only the selected GUI appearance identifier
    """

    def __init__(self, settings_dir: Path) -> None:
        self._path = settings_dir / "gui_v3_workspace.json"

        # Qt persistence blobs
        self.window_geometry: bytes | None = None
        # Legacy opaque Qt state is retained as an attribute for
        # compatibility but is deliberately never restored or re-saved.
        self.window_state: bytes | None = None
        # H-S69-B3A — explicit named floating-dock geometry only.
        self.named_workspace_layouts_v1: dict[str, dict] = {}
        # H-S69-B3B1 — last selected GUI-only preset and mode.
        self._last_workspace_presentation_v1: dict[str, str] | None = None
        # H-S69-B3C — application appearance only; never ProjectState.
        self._appearance_scheme_v1 = "light"

        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self._path.exists():
            return

        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))

            geom = data.get("geometry", "")
            self.window_geometry = (
                bytes.fromhex(geom) if isinstance(geom, str) and geom else None
            )
            # H-S69-B3A: old QMainWindow state blobs may encode obsolete
            # tab/split relationships and have caused native Qt faults.
            # Fail closed and replace them with named explicit geometry.
            self.window_state = None
            self.named_workspace_layouts_v1 = (
                _normalise_named_workspace_layouts_v1(
                    data.get("named_workspace_layouts_v1")
                )
            )
            self._last_workspace_presentation_v1 = (
                _normalise_last_workspace_presentation_v1(
                    data.get("last_workspace_presentation_v1")
                )
            )
            self._appearance_scheme_v1 = (
                _normalise_appearance_scheme_v1(
                    data.get("appearance_scheme_v1")
                )
            )
        except Exception:
            # Corrupt, incompatible, or partial — ignore silently
            self.window_geometry = None
            self.window_state = None
            self.named_workspace_layouts_v1 = {}
            self._last_workspace_presentation_v1 = None
            self._appearance_scheme_v1 = "light"

    def named_workspace_layout_v1(self, name: str) -> dict | None:
        stable_name = str(name or "").strip()
        layout = self.named_workspace_layouts_v1.get(stable_name)
        return deepcopy(layout) if layout is not None else None

    def set_named_workspace_layout_v1(
            self,
            name: str,
            layout: dict,
    ) -> bool:
        stable_name = str(name or "").strip()
        candidate = _normalise_named_workspace_layouts_v1({
            stable_name: layout,
        })
        if stable_name not in candidate:
            return False
        self.named_workspace_layouts_v1[stable_name] = candidate[stable_name]
        return True

    def last_workspace_presentation_v1(self) -> dict[str, str] | None:
        presentation = self._last_workspace_presentation_v1
        return deepcopy(presentation) if presentation is not None else None

    def set_last_workspace_presentation_v1(
            self,
            view_id: str,
            mode: str,
    ) -> bool:
        candidate = _normalise_last_workspace_presentation_v1({
            "view_id": view_id,
            "mode": mode,
        })
        if candidate is None:
            return False
        self._last_workspace_presentation_v1 = candidate
        return True

    def appearance_scheme_v1(self) -> str:
        return _normalise_appearance_scheme_v1(
            self._appearance_scheme_v1
        )

    def set_appearance_scheme_v1(self, scheme: str) -> bool:
        stable_scheme = str(scheme or "").strip().lower()
        if stable_scheme not in APPEARANCE_SCHEMES_V1:
            return False
        self._appearance_scheme_v1 = stable_scheme
        return True

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "geometry": self.window_geometry.hex()
            if self.window_geometry else "",
            # Keep the legacy key empty for older readers. Opaque Qt dock
            # state is intentionally retired by H-S69-B3A.
            "state": "",
            "named_workspace_layouts_v1": (
                _normalise_named_workspace_layouts_v1(
                    self.named_workspace_layouts_v1
                )
            ),
            "last_workspace_presentation_v1": (
                _normalise_last_workspace_presentation_v1(
                    self._last_workspace_presentation_v1
                )
                or {}
            ),
            "appearance_scheme_v1": (
                _normalise_appearance_scheme_v1(
                    self._appearance_scheme_v1
                )
            ),
        }

        try:
            self._path.write_text(
                json.dumps(data, indent=2),
                encoding="utf-8",
            )
        except Exception:
            # Persistence must never crash the GUI
            pass
