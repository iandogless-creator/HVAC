HVACgooee — GUI v3
Future Audit: Phase F-A → Phase G Constraints

Purpose of this audit
To explicitly record what Phase G (Authoritative Heat-Loss Execution) is not allowed to do, because Phase F-A proved a cleaner separation of concerns.

This document exists to prevent “just this once” shortcuts later.

1. Phase G May NOT Read GUI State
Locked by F-A

Phase F-A proved that all readiness information can be derived from ProjectState.

GUI panels expose presentation setters only, no getters, no retained meaning.

Therefore Phase G is forbidden to:

Read values from:

Heat-Loss panel widgets

Environment panel fields

Any GUI adapter cache

Infer intent from:

Enabled/disabled buttons

Preview text

Panel visibility or docking state

Rule: If Phase G needs information, it must come from ProjectState or an execution DTO, never from GUI memory.

2. Phase G May NOT Re-derive Semantics Already Proven in F-A
Locked by F-A

F-A established:

What “external design temperature exists” means

How reference ΔT is informationally derived

That readiness is composable and observable

Therefore Phase G is forbidden to:

Re-interpret “environment readiness”

Invent alternative definitions of ΔT for gating

Add hidden fallback logic like:

“If no outside temp, assume −3°C”

“If rooms disagree, take the mean”

Rule: Phase G consumes authoritative inputs, not heuristics.
Heuristics live only in preview/readiness phases.

3. Phase G May NOT Introduce Implicit Defaults
Locked by F-A

F-A explicitly forbade:

Automatic defaults

Silent assumptions

Background mutation

Therefore Phase G is forbidden to:

Auto-populate missing environment data

Guess room design temperatures

Fill construction layers implicitly

“Helpfully” proceed with partial data

Rule: If Phase G runs, all required inputs must already exist explicitly—or execution must fail loudly.

This is non-negotiable.

4. Phase G May NOT Mutate ProjectState Outside Its Authority Window
Locked by F-A

F-A established adapters as read-only observers

Execution authority is singular and explicit

Therefore Phase G is forbidden to:

Patch ProjectState opportunistically

Back-write derived values into intent fields

“Clean up” incomplete structures during execution

Instead:

Phase G may only:

Produce results

Emit result DTOs

Persist outputs in a clearly defined results domain

Rule: Intent is assembled before execution.
Execution does not fix intent.

5. Phase G May NOT Collapse Readiness and Execution
Locked by F-A

F-A separated:

“Is this meaningful to show?”

from

“Is this legal to execute?”

Therefore Phase G is forbidden to:

Perform readiness checks implicitly

Hide execution refusal behind silent no-ops

Combine validation + calculation in one opaque step

Instead:

Readiness must already be:

Explicit

User-visible

Explainable (Phase F-B / F-C)

Rule: If Phase G is invoked, it assumes readiness was already established.

6. Phase G May NOT Create New Cross-Panel Coupling
Locked by F-A

F-A proved cross-panel flow via shared authority, not direct wiring.

Therefore Phase G is forbidden to:

Notify panels directly

Push results into live GUI widgets

Coordinate UI updates across panels

Instead:

Phase G produces outputs

GUI observes results independently

Rule: Panels never talk to each other.
They only observe authority.

7. Phase G May NOT Change the Meaning of “Preview”
Locked by F-A

Preview ≠ calculation

Preview ≠ partial execution

Preview ≠ cached results

Therefore Phase G is forbidden to:

Reuse preview logic internally

Treat preview values as seeds

Optimise by “starting from preview ΔT”

Rule: Preview is epistemic.
Execution is physical.

8. Phase G May NOT Be Triggered Implicitly
Locked by F-A

“Run heat-loss” remains disabled in F-A

Execution is an explicit user act

Therefore Phase G is forbidden to:

Auto-run on project load

Auto-run on environment change

Auto-run as a side effect of UI navigation

Rule: Phase G runs because the user asked—not because the system noticed something.

Summary: What F-A Quietly Locked Forever

Because Phase F-A exists, Phase G must be:

Authoritative, not clever

Strict, not helpful

Explicit, not implicit

Deterministic, not heuristic

Headless-capable

GUI-agnostic

If Phase G ever needs to violate one of these rules, the correct response is:

“We need a new phase or a new authority—
not a shortcut.”
