# ======================================================================
# HVAC/gui_v3/adapters/education_panel_adapter.py
# ======================================================================

"""
HVACgooee — GUI v3
Education Panel Adapter — Education v1 (CANONICAL)

Responsibilities
----------------
• Resolve education text via education.resolver
• Inject read-only content into EducationPanel
• Manage Standard / Classical mode toggle
• NO calculations
• NO ProjectState authority
• NO GUI logic beyond panel calls
"""

from __future__ import annotations

from HVAC.education.resolver import resolve
from HVAC.gui_v3.panels.education_panel import EducationPanel


class EducationPanelAdapter:
    """
    Education adapter (GUI v3).

    This adapter is intentionally simple:
    - It does not store results
    - It does not interpret content
    - It only routes text
    """

    def __init__(
        self,
        *,
        panel: EducationPanel,
        domain: str,
        topic: str,
        mode: str = "standard",
    ) -> None:
        self._panel = panel

        self._domain = domain
        self._topic = topic
        self._mode = mode  # beginner | standard | classical

        # Wire UI → adapter
        self._panel.mode_changed.connect(self.set_mode)

        self.refresh()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """
        Resolve and push education content to the panel.
        """
        title, body = resolve(
            domain=self._domain,
            topic=self._topic,
            mode=self._mode,
        )

        self._panel.set_content(
            title=title,
            body=body,
            mode=self._mode,
        )

    # ------------------------------------------------------------------
    # Mode control (Standard / Classical)
    # ------------------------------------------------------------------

    def set_mode(self, mode: str) -> None:
        """
        Switch education mode.

        Parameters
        ----------
        mode:
            "beginner" | "standard" | "classical"
        """
        mode = mode.lower()
        if mode not in ("beginner", "standard", "classical"):
            return

        if mode == self._mode:
            return

        self._mode = mode
        self.refresh()

    def toggle_mode(self) -> None:
        """
        Convenience toggle (not required, but useful for shortcuts).
        """
        modes = ("beginner", "standard", "classical")
        index = modes.index(self._mode) if self._mode in modes else 0
        self.set_mode(modes[(index + 1) % len(modes)])

    # ------------------------------------------------------------------
    # Domain switching
    # ------------------------------------------------------------------

    def set_domain(self, domain: str) -> None:
        """
        Switch education domain while keeping the current topic.

        Used when dock visibility changes.
        """
        domain = domain.lower()
        if domain == self._domain:
            return

        self._domain = domain
        self.refresh()

    # ------------------------------------------------------------------
    # Topic / domain switching
    # ------------------------------------------------------------------

    def set_topic(self, *, domain: str, topic: str) -> None:
        """
        Change the education topic.

        Used when switching panels or modes.
        """
        domain = str(domain or "").lower()
        topic = str(topic or "").lower()
        if domain == self._domain and topic == self._topic:
            return
        self._domain = domain
        self._topic = topic
        self.refresh()
