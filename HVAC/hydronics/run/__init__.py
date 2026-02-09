"""
HVAC/gui/hydronics/__init__.py
-----------------------------

Hydronics GUI package (v1).

GUI rules (LOCKED):
- GUI never calls solvers directly.
- GUI talks ONLY to HydronicsOrchestratorV1.
- Calculations are event-driven; editing freezes outputs until commit.
- Pipe accumulation (totals/head/pump duty inputs) ONLY when system is stable.
"""

from __future__ import annotations
