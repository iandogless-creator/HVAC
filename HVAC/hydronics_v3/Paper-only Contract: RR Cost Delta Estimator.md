HVACgooee — Hydronics
Paper-only Contract: RR Cost Delta Estimator (No Touch to OperatingPoint / PressureDropPath)

Status: DRAFT (PAPER ONLY)
Scope: Hydronics proportioning / estimating layer (not GUI, not solvers)
Non-goal: No modification to OperatingPointEngineV1, PressureDropPathEngineV1, balancing, pump selection.

1. Purpose

Provide an estimate of how much additional pipework a reverse-return topology implies versus a direct-return topology, using existing hydronic topology knowledge and (optionally) existing path representations, without running full sizing/balancing.

This supports:

early feasibility / “is RR worth it?”

bill-of-quantities roughing

education/justification notes

2. Architectural Placement

Belongs to: HVAC/hydronics/proportioning/ (or equivalent “estimate” package)
Consumes: topology + length hints (not pressure-drop results)
Produces: immutable DTO results

Must NOT:

call OperatingPointEngineV1

call PressureDropPathEngineV1 for physics

compute friction, kv, pump head, etc.

mutate project intent or topology

influence schematic rendering (except optional display of results elsewhere)

3. Inputs (Conceptual)
3.1 Topology Snapshot (Required)

A read-only graph-like snapshot of:

nodes (boiler/plant, manifolds, rooms/emitters)

connections (pipes/edges)

grouping (system/leg/subleg)

This can be sourced from the same upstream “authoritative hydronics assembly” that later feeds PressureDropPathEngineV1, but must be a stable DTO, not engine internals.

3.2 Length Basis (Choose One)

Estimator supports multiple “length bases”:

A) Declared lengths (best early option)

user/project provides nominal lengths per connection or per group

B) Geometry-derived lengths (later, if you have geometry)

lengths derived outside estimator, passed in

C) Heuristic defaults (allowed, but must be explicit)

e.g., “assume each riser segment = 3.0 m per floor”

must be tagged as heuristic

4. Definitions (LOCKED)
Direct Return (DR)

Return path follows the shortest / most direct return to source/header, without intentional equalization routing.

Reverse Return (RR)

Return path is routed such that the first supply branch is the last to return, creating approximate equalization by geometry.

Important: The estimator does not validate whether RR is “correct”; it only estimates length deltas given an RR routing rule.

5. Output DTOs (Paper Shapes)
5.1 RRDeltaResultDTO (Top-level)

Represents a single estimator run.

Fields:

basis: enum-like (DECLARED, GEOMETRY, HEURISTIC)

scope: enum-like (SYSTEM, GROUP_SET)

direct_total_m: float

reverse_total_m: float

delta_m: float (reverse - direct)

delta_pct: float | None (if direct_total_m > 0)

notes: list[str] (human readable, non-authoritative)

breakdown: list[RRDeltaGroupBreakdownDTO]

5.2 RRDeltaGroupBreakdownDTO

Optional breakdown per group level (leg/subleg/zone).

Fields:

group_id: opaque

group_label: str (display only)

direct_m: float

reverse_m: float

delta_m: float

assumptions: list[str] (e.g., “return header assumed same length as flow header”)

5.3 RRDeltaAssumptionDTO (Optional formalization)

If you want stricter auditing later:

Fields:

key: str (e.g., RiserHeightPerStoreyM)

value: float | str

source: enum-like (USER, DEFAULT, PROJECT_TEMPLATE)

applies_to: SYSTEM|GROUP|EDGE

6. Estimator Engine Contract
Name

RRCostDeltaEstimatorV1

Responsibility

Given a topology snapshot and length basis, compute DR and RR total lengths under declared routing rules.

Public entry point (conceptual)

estimate(topology, length_basis, scope) -> RRDeltaResultDTO

No side effects.

7. Routing Rules (Estimator Logic Rules, Non-Physics)

These are graph rules, not hydraulics.

7.1 Group Scoping

Estimator may compute RR deltas for:

whole system

selected group set (e.g., a leg with sublegs)

RR routing must not cross group boundaries unless the run scope explicitly includes them.

7.2 Manifolds / Headers

Manifold nodes are treated as:

distribution junctions

optional “return header counterpart” (if modelled)

If return header is not explicit:

estimator may assume return header length = flow header length (assumption recorded)

7.3 Riser Markers

Riser markers are not pipes by default.
If vertical length is included:

it must come from explicit basis/assumption

it must be disclosed as heuristic/geometry basis

8. How It “Plugs Into” OperatingPoint / PressureDropPath — Without Touching Them

The plug-in point is upstream of those engines:

PressureDropPathEngineV1 consumes topology + sizing/physics data to compute paths.

This estimator consumes the same topology snapshot, but only reads:

connectivity

group membership

edge nominal lengths

So both can share:

HydronicTopologySnapshotDTO (or similarly named DTO)

GroupGraphDTO

EdgeLengthDTO

…but RRDeltaEstimator must never import or call the engines.

Dependency direction stays clean:

Topology DTOs  →  RRDeltaEstimatorV1
Topology DTOs  →  PressureDropPathEngineV1
(no cross-calls)

9. Presentation (What GUI May Show, Later)

GUI panels may optionally display:

delta_m

delta_pct

group breakdown

But must label as:

“Estimate”

“Based on declared/heuristic/geometry lengths”

“Non-authoritative”

The schematic panel must never compute it; at most it can display an annotation if provided.

10. Success Criteria (for v1 of this estimator)

Produces stable RR-vs-DR length deltas from topology + lengths

Works without any pipe sizing or balancing results

Clearly records assumptions

Cannot affect any authoritative engines

Testable with small synthetic graphs

11. Freeze Statement

RRCostDeltaEstimatorV1 is a proportioning estimator only.
It must remain independent of:

PressureDropPathEngineV1

OperatingPointEngineV1

Pump selection

Balancing engines

GUI panels

Any coupling requires a new bootstrap.

If you want next, I can also draft a Topology Snapshot DTO contract (paper-only) that both the estimator and PressureDropPath can consume, to keep that shared boundary crisp without refactoring either side.
