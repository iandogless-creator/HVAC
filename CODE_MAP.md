# HVACgooee — Code Map

This file identifies the current active code path.

For current project status, see `CURRENT_STATE.md`.

---

## Current GUI entry point

`HVAC/gui_v3/run_gui_v3.py`

Runs the current PySide6 GUI.

---

## Main GUI shell

`HVAC/gui_v3/main_window.py`

Owns:

- dock/panel creation
- DEV mode switching
- signal wiring
- overlay routing
- project open/save menu actions

---

## Runtime authority

`HVAC/project/project_state.py`

The central engineering authority.

Owns:

- rooms
- environment
- boundary segments
- constructions
- heat-loss results/lifecycle state
- `project_dir`

Rule:

`ProjectState` owns engineering state. GUI panels do not.

---

## GUI context

`HVAC/gui_v3/context/gui_project_context.py`

GUI-only coordination layer.

Owns:

- current room focus
- project change signals
- edit requests
- construction focus
- adjacency edit requests

Does not own engineering calculations or engineering data.

---

## Heat-loss panel

`HVAC/gui_v3/panels/heat_loss_panel.py`

Displays:

- Element
- Area
- U-value
- ΔT
- Qf
- ΣQf / Qv / Qt

Current UI convention:

- Construction IDs are hidden from the table.
- Adjacency is shown in the Element column, e.g. `Wall → Middle`.
- ΔT column click opens adjacency editing where applicable.

---

## Heat-loss adapter

`HVAC/gui_v3/adapters/heat_loss_panel_adapter.py`

Projects `ProjectState` into the heat-loss panel.

Current responsibilities:

- builds display rows
- attaches worksheet row metadata
- projects adjacent room labels
- computes live fallback totals when no authoritative run result exists
- routes HLP click intent

---

## DEV scenario switching

`HVAC/dev/bootstrap_dev_project.py`

Main DEV scenario dispatcher.

`HVAC/dev/bootstrap_registry.py`

Maps DEV mode names to bootstrap builders.

`HVAC/dev/bootstrap_vertical_3room.py`

Vertical adjacency DEV scenario.

`HVAC/dev/dev_constructions.py`

Canonical DEV construction definitions.

---

## Fabric projection

`HVAC/fabric/generate_fabric_from_topology.py`

Current topology-to-fabric bridge.

Turns boundary segments into fabric rows for HLP projection.

---

## Topology

`HVAC/topology/`

Current topology model and helpers.

Important files include:

- `boundary_segment_v1.py`
- `topology_resolver_v1.py`
- `topology_symmetry_enforcer_v1.py`
- `topology_validator_v1.py`

Boundary segments own adjacency.

---

## Construction authority

`HVAC/core/construction_v1.py`

Canonical construction object.

`ProjectState.constructions`

Owns construction definitions.

Rule:

U-values resolve through construction IDs. Surface rows do not own U-values directly.

---

## Historical docs

Older design/freeze notes may exist under `docs/`.

Those files are retained for project history and may not describe the current active code path.
