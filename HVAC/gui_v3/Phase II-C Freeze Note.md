======================================================================
HVACgooee — Phase II-C Freeze Note
Title: Fabric Engine Formalisation (U × A × ΔT, ΣQf)
Status: FROZEN (CANONICAL)
Applies to: heatloss/engines + heatloss/dto
Date: Wednesday 26 February 2026, 20:00 pm (UK)
======================================================================

1. Purpose of This Freeze

Phase II-C freezes the *fabric heat-loss physics contract* and its
deterministic DTO outputs.

This phase introduces no new GUI behaviour, no readiness rules,
no persistence, and no ventilation/infiltration terms.

2. Scope (Frozen)

2.1 In Scope
• FabricHeatLossEngine.run(inputs) -> FabricHeatLossResultDTO
• Per-surface Qf calculation: Qf = U × A × ΔT
• Project aggregation: ΣQf = sum(Qf)
• Deterministic rollups by room (pure convenience views)

2.2 Out of Scope (Explicit)
• Ventilation / infiltration heat loss
• Thermal mass / dynamic response
• Solar gains, internal gains
• Emitter sizing, hydronics coupling
• ProjectState readiness evaluation
• GUI rendering, worksheet layout, or formatting

3. Canonical Inputs (Locked)

The engine consumes FabricHeatLossInputDTO which must provide:
• project_id
• internal_design_temp_C (Ti)
• external_design_temp_C (Te)
• surfaces: list[FabricSurfaceInputDTO] containing:
  - surface_id, room_id, surface_class
  - area_m2 (A)
  - u_value_W_m2K (U)

ΔT is defined as:
  ΔT = Ti - Te
and must be > 0 for execution.

4. Canonical Physics (Locked)

For each surface:
  Qf(W) = U(W/m²K) × A(m²) × ΔT(K)

No additional multipliers or correction factors are permitted in Phase II-C.

5. Canonical Outputs (Locked)

FabricHeatLossResultDTO must include:
• surfaces: list[FabricSurfaceResultDTO] (one per input surface)
• total_qf_W = Σ Qf
• total_area_m2 = Σ A
• qf_by_room_W, area_by_room_m2 (pure rollups)

6. Purity Rules (Locked)

FabricHeatLossEngine:
• Must not reference ProjectState
• Must not call readiness evaluation
• Must not mutate inputs
• Must not perform IO or persistence
• Must be deterministic for identical inputs

7. Completion Criteria (Satisfied by Contract)
✔ Surface Qf computed by U×A×ΔT
✔ ΣQf computed by summation only
✔ DTOs are stable and explicit
✔ Engine is pure and side-effect free

======================================================================
Phase II-C is now frozen.
Any modification to the physics contract requires Phase II-D.
======================================================================
