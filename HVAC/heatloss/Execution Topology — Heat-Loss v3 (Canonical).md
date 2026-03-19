GUI (Panels)
 → Adapters (presentation only)
   → Intent DTOs (Ti, Te, ACH, selections)
   → Readiness Evaluation (pure, non-mutating)
   → Controller (orchestrator)
     → Build runner input DTOs
       • FabricHeatLossInputDTO
       • VentilationACHInputDTO
     → Runners (pure)
       → Result DTOs
     → Explicit commit to ProjectState
GUI refreshes strictly from ProjectState

Fabric Runner Preconditions

At least one ResolvedFabricSurface present

ΔT > 0 (Ti > Te)

U-values resolved

Geometry is frozen