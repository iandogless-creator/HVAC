HVACgooee — Bootstrap: Repopulating Heat-Loss (Qf) Panel

Timestamp: Tuesday 11 March 2026 (UK)
Project: HVACgooee
Subsystem: GUI v3 → Heat-Loss Worksheet Integration

Current State

The system successfully generates fabric elements from room geometry and topology.

Working pipeline:

Geometry (RoomState.geometry)
      ↓
Boundary segments
      ↓
Topology fabric bridge
      ↓
room.fabric_elements
      ↓
HeatLossPanelAdapter
      ↓
Heat-Loss worksheet rows

Console confirms:

Projected surfaces: 5
[FabricElements] room_A count=5
[HL Worksheet] room=room_A rows=5

So the fabric projection and worksheet row generation are functioning correctly.

Panel Authority Model

Environment Panel
• Authoritative: Te (external design temperature)

Geometry Mini Panel
• Length
• Width
• Height
• External wall length
• Ti (room internal design temperature)

ACH Mini Panel
• ACH override

Heat-Loss Panel (HLP)
• Read-only worksheet display
• ΣQf / Qv / Qt results
• Run Heat-Loss button

HLP does not edit modelling inputs.

Worksheet Columns
Element | A (m²) | U (W/m²K) | ΔT (K) | Qf (W)

Current behaviour:

• A and U populate correctly
• ΔT currently unresolved
• Qf populated only after running the engine

ΔT Rule (Phase IV)

For current development stage:

External surfaces → ΔT = Ti − Te
Internal surfaces → handled later by adjacency wizard

Example:

Ti = 21°C
Te = -3°C

ΔT = 24 K
Desired Behaviour

When a room is selected:

Geometry
   ↓
Fabric elements
   ↓
Worksheet rows populated

Example worksheet:

external_wall   9.6   0.28   24
external_wall   9.6   0.28   24
external_wall   7.2   0.28   24
floor          12.0   0.18   24
roof           12.0   0.18   24

Before pressing Run:

Qf column remains blank

After pressing Run:

Qf = U × A × ΔT
ΣQf populated
Qv populated
Qt populated
Adapter Responsibilities

HeatLossPanelAdapter must:

Resolve effective temperatures

Ti → from RoomState
Te → from EnvironmentState

Compute ΔT

delta_t = Ti − Te

Build worksheet rows

surface_id
element
A
U
ΔT
Qf=None

Send rows to panel

panel.set_rows(rows)
Refresh Flow

Worksheet repopulates when:

Room selection changes
Geometry changes
ACH changes
Heat-loss run completes

Trigger:

MainWindowV3._refresh_all_adapters()
Next Development Steps

Ensure ΔT auto-resolves in adapter

Confirm worksheet repopulates on room change

Keep HLP read-only (inputs moved to mini panels)

Integrate FabricHeatLossEngine results overlay

Display ΣQf / Qv / Qt totals

Goal of Next Session

Stabilise the Qf worksheet population cycle so that:

Room change → worksheet instantly repopulates
Run heat-loss → Qf results overlay correctly

The geometry → fabric → worksheet chain is already operational.
