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
    # H-S69-B3D — one safe, GUI-only user exploded workspace.
    "user",
})
WORKSPACE_VIEW_MODES_V1 = frozenset({"docked", "exploded"})
APPEARANCE_SCHEMES_V1 = frozenset({"light", "dark"})


def _normalise_appearance_scheme_v1(value: object) -> str:
    scheme = str(value or "").strip().lower()
    return scheme if scheme in APPEARANCE_SCHEMES_V1 else "light"


def _normalise_workspace_panel_sets_v1(
        value: object,
) -> dict[str, list[str]]:
    """Return bounded GUI-only panel membership for factory docked views."""
    if not isinstance(value, dict):
        return {}
    result: dict[str, list[str]] = {}
    for raw_storage_id, raw_panel_ids in value.items():
        storage_id = str(raw_storage_id or "").strip()
        view_id, separator, mode = storage_id.partition(":")
        if (
            not separator
            or view_id not in WORKSPACE_VIEW_IDS_V1
            or view_id == "user"
            or mode != "docked"
            or not isinstance(raw_panel_ids, (list, tuple))
        ):
            continue
        panel_ids: list[str] = []
        for raw_panel_id in raw_panel_ids[:64]:
            panel_id = str(raw_panel_id or "").strip()
            if (
                panel_id
                and len(panel_id) <= 128
                and panel_id not in panel_ids
            ):
                panel_ids.append(panel_id)
        if panel_ids:
            result[storage_id] = panel_ids
    return result


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
    # The user workspace deliberately stores explicit floating geometry only.
    if view_id == "user" and mode != "exploded":
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
            layout = {
                "schema": NAMED_WORKSPACE_LAYOUT_SCHEMA_V1,
                "docks": docks,
            }
            # H-S69-B3E — optional bounded user override of stable GUI dock
            # identities. Unknown or malformed identities are ignored later
            # by the owning main window; no ProjectState meaning is stored.
            raw_panel_ids = raw_layout.get("panel_ids")
            if isinstance(raw_panel_ids, (list, tuple)):
                panel_ids: list[str] = []
                for raw_panel_id in raw_panel_ids[:64]:
                    panel_id = str(raw_panel_id or "").strip()
                    if (
                        panel_id
                        and len(panel_id) <= 128
                        and panel_id not in panel_ids
                    ):
                        panel_ids.append(panel_id)
                if panel_ids:
                    layout["panel_ids"] = panel_ids
            layouts[name] = layout
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
        # H-S69-B3F — user panel membership for factory docked views.
        self.workspace_panel_sets_v1: dict[str, list[str]] = {}
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
            self.workspace_panel_sets_v1 = (
                _normalise_workspace_panel_sets_v1(
                    data.get("workspace_panel_sets_v1")
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
            self.workspace_panel_sets_v1 = {}
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

    def workspace_panel_set_v1(
            self,
            storage_id: str,
    ) -> tuple[str, ...] | None:
        stable_id = str(storage_id or "").strip()
        panel_ids = self.workspace_panel_sets_v1.get(stable_id)
        return tuple(panel_ids) if panel_ids is not None else None

    def set_workspace_panel_set_v1(
            self,
            storage_id: str,
            panel_ids: list[str] | tuple[str, ...],
    ) -> bool:
        stable_id = str(storage_id or "").strip()
        candidate = _normalise_workspace_panel_sets_v1({
            stable_id: panel_ids,
        })
        if stable_id not in candidate:
            return False
        self.workspace_panel_sets_v1[stable_id] = candidate[stable_id]
        return True

    def clear_workspace_panel_set_v1(self, storage_id: str) -> bool:
        stable_id = str(storage_id or "").strip()
        return self.workspace_panel_sets_v1.pop(stable_id, None) is not None

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
            "workspace_panel_sets_v1": (
                _normalise_workspace_panel_sets_v1(
                    self.workspace_panel_sets_v1
                )
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
