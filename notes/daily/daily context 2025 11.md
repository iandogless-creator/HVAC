# daily_context_2025-11-18 (notes/daily)

## Purpose

Bootstrap context for continuing the HVAC/Gooee project each morning with **full continuity** but without needing to reload the entire 1.5MB chat history.

## Summary Snapshot

* Current project focus: **NodeView + Gooee GUI foundation**
* Latest completed steps:

  * NodeView grid + zoom + pan
  * Node snapping to grid
  * Model separation strategy confirmed
  * Daily logging system established
* Immediate next actions (choose any when resuming):

  1. Add model references to NodeItem
  2. Add right‑click menu (delete / duplicate / rename)
  3. Add connector line class
  4. Add JSON save/load layout
  5. Bind NodeView to real Room/Pipe classes

## Architectural anchor

```
UI (NodeView) → represents → Model (Room/Pipe/System)

Node drag moves visuals only
Solver runs when user requests
No hidden recalcs
No corruption risk
```

## Data + UI rules

* Node position syncs to model but **does not trigger auto-recalc**
* Pipe solver reads latest geometry when requested
* Future GUI will allow:

  * Fitting selection
  * K-value input
  * Effective length auto-calc
  * Hybrid manual & auto routing

## Daily reminder

If lost, ask:

> "Load Daily Context Bootstrap"

…and we instantly continue at full depth.

---

(End of bootstrap file — add new notes below this line each day if desired)

