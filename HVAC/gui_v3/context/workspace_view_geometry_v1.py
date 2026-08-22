from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class WorkspaceScreenGeometryV1:
    name: str
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class ResolvedDockGeometryV1:
    screen_name: str
    x: int
    y: int
    width: int
    height: int
    used_fallback_screen: bool = False


def _clamped_geometry_v1(
        *,
        screen: WorkspaceScreenGeometryV1,
        x: int,
        y: int,
        width: int,
        height: int,
        used_fallback_screen: bool,
) -> ResolvedDockGeometryV1:
    width = max(240, min(int(width), screen.width))
    height = max(80, min(int(height), screen.height))
    x = max(screen.x, min(int(x), screen.x + screen.width - width))
    y = max(screen.y, min(int(y), screen.y + screen.height - height))
    return ResolvedDockGeometryV1(
        screen_name=screen.name,
        x=x,
        y=y,
        width=width,
        height=height,
        used_fallback_screen=used_fallback_screen,
    )


def resolve_exploded_dock_geometry_v1(
        *,
        saved_geometry: dict | None,
        screens: tuple[WorkspaceScreenGeometryV1, ...],
        dock_index: int,
        dock_count: int,
) -> ResolvedDockGeometryV1 | None:
    """Resolve one safe floating-dock rectangle for one or two+ screens."""
    if not screens:
        return None

    saved = saved_geometry if isinstance(saved_geometry, dict) else None
    if saved is not None:
        requested_name = str(saved.get("screen_name") or "")
        requested_screen = next(
            (screen for screen in screens if screen.name == requested_name),
            None,
        )
        fallback = requested_screen is None
        screen = requested_screen or screens[0]
        return _clamped_geometry_v1(
            screen=screen,
            x=int(saved.get("x", screen.x)),
            y=int(saved.get("y", screen.y)),
            width=int(saved.get("width", screen.width)),
            height=int(saved.get("height", screen.height)),
            used_fallback_screen=fallback,
        )

    margin = 18
    gap = 12
    count = max(1, int(dock_count))
    index = max(0, min(int(dock_index), count - 1))

    if len(screens) >= 2:
        # The primary working panel occupies display 1. Companion panels
        # tile on display 2, matching Ian's normal dual-1080p workspace.
        if index == 0:
            screen = screens[0]
            return _clamped_geometry_v1(
                screen=screen,
                x=screen.x + margin,
                y=screen.y + margin,
                width=screen.width - 2 * margin,
                height=screen.height - 2 * margin,
                used_fallback_screen=False,
            )
        screen = screens[1]
        tile_index = index - 1
        tile_count = max(1, count - 1)
    else:
        screen = screens[0]
        tile_index = index
        tile_count = count

    columns = 1 if tile_count == 1 else 2
    rows = max(1, ceil(tile_count / columns))
    cell_width = max(240, (screen.width - 2 * margin - gap * (columns - 1)) // columns)
    cell_height = max(160, (screen.height - 2 * margin - gap * (rows - 1)) // rows)
    column = tile_index % columns
    row = tile_index // columns
    return _clamped_geometry_v1(
        screen=screen,
        x=screen.x + margin + column * (cell_width + gap),
        y=screen.y + margin + row * (cell_height + gap),
        width=cell_width,
        height=cell_height,
        used_fallback_screen=False,
    )
