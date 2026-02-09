# GUI v2 Adapters — LOCKED (Jan 2026)

This directory intentionally contains **NO active adapters**.

## Historical note
Early GUI v2 builds used adapter-style modules
(e.g. heatloss_to_hydronics_v1.py) to mutate
ProjectState and GuiViewState.

This pattern is **deprecated and forbidden**.

## Current contract (LOCKED)

• ProjectState is mutated **only by runners / engines**
• GuiViewState is **presentation-only**
• MainWindowV2 is the ONLY legal bridge between:
  GUI panels ↔ ProjectState

## Heat-Loss → Hydronics handover

• Heat-loss runner commits Qt into ProjectState
• Hydronics reads ProjectState directly
• GUI never passes Qt between panels

If you think you need an adapter here:
👉 the architecture is being violated.
