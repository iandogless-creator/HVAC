# ======================================================================
# HVACgooee — GUI Settings (GUI v3)
# Phase: E/F — Workspace Persistence
# Status: CANONICAL
# ======================================================================
# NOTE: Styling / appearance preferences intentionally deferred.
from __future__ import annotations

from pathlib import Path
import json


class GuiSettings:
    """
    GUI-only persistence container.

    Responsibilities
    ----------------
    • Store QMainWindow geometry & dock layout
    • Best-effort restore
    • No ProjectState knowledge
    • No panel knowledge
    • No styling or appearance concerns
    """

    def __init__(self, settings_dir: Path) -> None:
        self._path = settings_dir / "gui_v3_workspace.json"

        # Qt persistence blobs
        self.window_geometry: bytes | None = None
        self.window_state: bytes | None = None

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
            state = data.get("state", "")

            self.window_geometry = (
                bytes.fromhex(geom) if isinstance(geom, str) and geom else None
            )
            self.window_state = (
                bytes.fromhex(state) if isinstance(state, str) and state else None
            )
        except Exception:
            # Corrupt, incompatible, or partial — ignore silently
            self.window_geometry = None
            self.window_state = None

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "geometry": self.window_geometry.hex()
            if self.window_geometry else "",
            "state": self.window_state.hex()
            if self.window_state else "",
        }

        try:
            self._path.write_text(
                json.dumps(data, indent=2),
                encoding="utf-8",
            )
        except Exception:
            # Persistence must never crash the GUI
            pass
