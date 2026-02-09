"""
Hydronics v1+

Canonical execution entry point:
    HVAC/hydronics/run/hydronics_runner_v1.py

All legacy network-based and GUI-coupled engines
have been intentionally removed.

Hydronics GUI package (v1).

GUI rules (LOCKED):
- GUI never calls solvers directly.
- GUI talks ONLY to HydronicsRunnerV1.
- Calculations are event-driven; editing freezes outputs until commit.
- Pipe accumulation (totals/head/pump duty inputs) ONLY when system is stable.
"""
