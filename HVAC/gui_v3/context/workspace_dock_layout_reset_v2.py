from __future__ import annotations

from collections.abc import Iterable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QMainWindow,
    QScrollArea,
)


def reset_workspace_docks_v2(
        window: QMainWindow,
        docks: Iterable[QDockWidget],
) -> None:
    """Detach docks completely so a named view starts without stale tabs."""
    seen: set[int] = set()
    for dock in docks:
        identity = id(dock)
        if identity in seen:
            continue
        seen.add(identity)

        dock.hide()
        if dock.isFloating():
            dock.setFloating(False)
        window.removeDockWidget(dock)



_NAMED_SIDE_SCROLL_PROPERTY_V2 = "hvacNamedWorkspaceSideScrollV2"


def _set_named_side_scroll_v2(
        dock: QDockWidget,
        *,
        enabled: bool,
) -> None:
    """Make dense Side contents scrollable without changing panel ownership."""
    current = dock.widget()
    if current is None:
        return
    is_wrapper = bool(current.property(_NAMED_SIDE_SCROLL_PROPERTY_V2))

    if enabled and not is_wrapper:
        wrapper = QScrollArea(dock)
        wrapper.setProperty(_NAMED_SIDE_SCROLL_PROPERTY_V2, True)
        wrapper.setWidgetResizable(True)
        wrapper.setFrameShape(QFrame.NoFrame)
        wrapper.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        wrapper.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        wrapper.setWidget(current)
        dock.setWidget(wrapper)
        return

    if not enabled and is_wrapper:
        panel = current.takeWidget()
        if panel is not None:
            dock.setWidget(panel)
        current.deleteLater()


def apply_named_workspace_docks_v2(
        window: QMainWindow,
        *,
        all_docks: Iterable[QDockWidget],
        main_dock: QDockWidget,
        side_docks: Sequence[QDockWidget],
        bottom_docks: Sequence[QDockWidget],
) -> tuple[QDockWidget, ...]:
    """Build Side-left, Main-upper-right and Bottom-lower-right."""
    sides = tuple(side_docks)
    bottoms = tuple(bottom_docks)
    if len(sides) > 2 or len(bottoms) > 2:
        raise ValueError("Named workspace supports two Side and two Bottom panels")

    visible = (main_dock,) + sides + bottoms
    side_identities = {id(dock) for dock in sides}
    for dock in visible:
        _set_named_side_scroll_v2(
            dock,
            enabled=id(dock) in side_identities,
        )
        # An explicit dock minimum overrides the much larger aggregate
        # minimumSizeHint supplied by dense real panel contents.  Users can
        # still enlarge either side of every splitter when editing a panel.
        dock.setMinimumSize(160, 80)

    window.setDockNestingEnabled(True)
    reset_workspace_docks_v2(window, all_docks)
    window.addDockWidget(Qt.RightDockWidgetArea, main_dock)

    if sides:
        window.addDockWidget(Qt.LeftDockWidgetArea, sides[0])
        if len(sides) > 1:
            window.addDockWidget(Qt.LeftDockWidgetArea, sides[1])
            window.splitDockWidget(sides[0], sides[1], Qt.Vertical)

    if bottoms:
        window.addDockWidget(Qt.RightDockWidgetArea, bottoms[0])
        window.splitDockWidget(main_dock, bottoms[0], Qt.Vertical)
        if len(bottoms) > 1:
            window.addDockWidget(Qt.RightDockWidgetArea, bottoms[1])
            window.splitDockWidget(bottoms[0], bottoms[1], Qt.Horizontal)

    for dock in visible:
        dock.show()
    return visible
