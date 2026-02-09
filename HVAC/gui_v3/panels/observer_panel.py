"""
HVACgooee — GUI v3
Observer Panel (Preferences Only)

Purpose
-------
Installation-level preferences panel for GUI behaviour
and appearance.

This panel exists solely to allow the user to adjust
non-authoritative UI preferences. It has no knowledge
of engineering intent, project data, or results.

All preferences modified here apply to the local
installation only and are never stored in ProjectState.

May display / modify (installation-level only):
- Theme (dark / light)
- Accent scheme selection
- Panel visibility and persistence
- Window layout preferences
- Education panel behaviour settings
- Display / formatting preferences (UI only)

Must NOT:
- Read or write ProjectState
- Display project data or results
- Trigger calculations or engines
- Modify any value used by engineering logic
- Act as an object inspector
- Establish precedent for domain editing

Status
------
NOT IMPLEMENTED.

This file intentionally contains no UI logic.
Implementation must strictly follow the GUI v3
Observer Phase bootstrap.
"""


class ObserverPanel:
    """
    Preferences-only observer panel.

    This panel is invoked via the header menu
    and is optional. It must never be required
    for understanding project data or results.
    """

    def __init__(self, *args, **kwargs):
        pass