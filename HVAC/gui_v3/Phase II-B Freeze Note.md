======================================================================
HVACgooee — Phase II-B Freeze Note
Title: Heat-Loss Readiness → Execution Wiring
Status: FROZEN (CANONICAL)
Applies to: ProjectState, GUI v3, Controllers
Date: Monday 24 February 2026, 22:15 pm (UK)
======================================================================

1. Purpose of This Freeze
------------------------

Phase II-B freezes the authoritative contract that governs how heat-loss
readiness transitions into execution.

This phase completes the readiness lifecycle introduced in Phase I-C and
extended in Phase II-A by formally binding:

• ProjectState readiness evaluation
• GUI run gating
• Execution permission

Phase II-B ensures that **no heat-loss execution can occur unless readiness
is explicitly satisfied**, and that this rule is enforced consistently across
GUI, adapters, and controllers.

This freeze exists to prevent:

• implicit or duplicated readiness checks
• execution from partially-defined project state
• GUI-side heuristics
• controller-level guesswork
• future divergence between “can run” and “did run”

2. Scope (Exactly What Is Frozen)
--------------------------------
2.1 In Scope

• Readiness → Run button gating
• ProjectHeatLossReadinessAdapter behaviour
• HeatLossReadiness DTO semantics
• Execution permission rules
• GUI → Controller execution contract

2.2 Explicitly Out of Scope

• Heat-loss physics
• Fabric resolution engines
• Construction authoring
• U-value derivation
• Result persistence
• Hydronics execution

None of the above may be retroactively introduced into Phase II-B.

3. Canonical Readiness Object (LOCKED)
-------------------------------------

Heat-loss readiness is represented exclusively by a concrete domain object:

    HeatLossReadiness

This object is created only by:

    ProjectState.evaluate_heatloss_readiness()

The readiness object has the following locked attributes:

• is_ready : bool
• blocking_reasons : list[str]

There are:

• no dict-like payloads
• no optional fields
• no alternate readiness shapes
• no implicit defaults

Any change to this object requires a new phase.

4. Single Source of Truth (LOCKED)
---------------------------------

ProjectState is the single authority for determining readiness.

Rules:

• Readiness evaluation is non-mutating
• Readiness evaluation has no GUI knowledge
• Readiness evaluation has no execution knowledge
• Controllers MUST NOT re-evaluate readiness

Execution code must assume:

    “If execution was invoked, readiness was already true.”

5. ProjectHeatLossReadinessAdapter (LOCKED)
-------------------------------------------

The ProjectHeatLossReadinessAdapter is the only component permitted to:

• Translate HeatLossReadiness into GUI state
• Gate the Run Heat-Loss action
• Present blocking reasons
• Surface the “Fix U-Values…” affordance

The adapter:

• Reads ProjectState only
• Never mutates ProjectState
• Performs no heuristics
• Performs no inference
• Performs no fallback logic

The adapter MUST access readiness via:

• readiness.is_ready
• readiness.blocking_reasons

Any defensive tolerance (dicts, alternate names, etc.) is explicitly forbidden.

6. GUI Behaviour (LOCKED)
------------------------

6.1 Run Button Gating

• Run Heat-Loss is enabled if and only if readiness.is_ready == True
• Disabled otherwise

6.2 Blocking Presentation

When readiness.is_ready == False:

• Blocking reasons are displayed verbatim
• No filtering or inference is applied
• Ordering is preserved

6.3 Fix Action

If any blocking reason references missing U-values:

• A “Fix U-Values…” affordance may be shown
• This emits the same navigation intent as Phase II-A

There are:

• no repair-only execution paths
• no bypass mechanisms
• no silent execution modes

7. Execution Contract (LOCKED)
------------------------------

Controllers are permitted to execute heat-loss calculations only when invoked
via the GUI Run action.

Controllers MUST:

• Assume readiness is satisfied
• NOT call evaluate_heatloss_readiness()
• NOT inspect readiness state
• NOT re-check U-values or fabric completeness

Any execution initiated outside this contract violates Phase II-B.

8. Failure Modes (LOCKED)
------------------------

If ProjectState is missing:

• Execution is disabled
• Readiness reports “No project loaded”

If readiness.is_ready == False:

• Execution is impossible
• GUI remains blocked

There are no “best-effort” runs.

9. Phase II-B Completion Criteria (Satisfied)
--------------------------------------------

✔ Readiness is evaluated in exactly one place
✔ Run button is gated solely by readiness
✔ Controllers never re-check readiness
✔ Blocking reasons are explicit and deterministic
✔ No dict-based or heuristic readiness handling
✔ Phase II-A navigation contracts remain intact
✔ Readiness → Execution boundary is unambiguous

10. Forward Reference (Not Part of This Freeze)
-----------------------------------------------

Subsequent phases may introduce:

• Heat-loss execution engines
• Result DTOs
• Persistence of run results
• ΣQf / Qv / Qt aggregation
• Hydronics execution coupling

None of these may modify Phase II-B readiness or execution rules.

======================================================================
Phase II-B is now frozen.
Readiness and execution are formally decoupled and enforced.
======================================================================
