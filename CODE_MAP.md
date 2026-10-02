# HVACgooee — Code Map

This file identifies the current active code path.

For current project status, see `CURRENT_STATE.md`.

## H-S74-A Topology guidance and Education

- `HVAC/education/topology_guidance_v1.py`: five guide steps and eight concise
  topics at Beginner/Standard/Classical levels; text only, no ProjectState.
- `HVAC/education/resolver.py`: routes the topology domain.
- `HVAC/gui_v3/widgets/topology_room_drag_drop_interaction_v1.py`: explicit dark
  text for the existing pale staging tray in either appearance scheme.
- `HVAC/gui_v3/panels/topology_arranger_panel.py`: persistent-preference signal,
  guided visibility of existing controls, Back/Next and field-help identifiers.
- `HVAC/gui_v3/adapters/topology_arranger_panel_adapter.py`: resets presentation
  drafts/selection on project swap; existing engineering action paths retained.
- `HVAC/gui_v3/main_window.py`: owns Wizard QSettings persistence, field-level
  topic routing, retained topic inside Education and explicit help display.
- `HVAC/dev/test_hs74a_topology_guidance_v1.py`: topic coverage, presentation-only
  navigation, direct-mode parity, explicit creation and project lifecycle.
- `HVAC/dev/test_hs74a_topology_help_integration_v1.py`: actual MainWindow focus,
  help/level controls, floating placement and fresh-process preferences.

## H-S73-A pump preview path

- `HVAC/gui_v3/widgets/pump_preview_widget_v1.py`: Pump tab observer and intent
  editor, hosted by `HydronicsSchematicPanel`.
- `HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py`: routes explicit
  Apply/Clear requests and formats controller results.
- `HVAC/hydronics/pumps/pump_preview_controller_v1.py`: committed-snapshot
  readiness, no-double-counted flow source, snapshot binding and intent writes.
- `HVAC/hydronics/pumps/pump_preview_runner_v1.py`: pure flow/head arithmetic.
- `HVAC/hydronics/pumps/pump_preview_basis_v1.py`: optional persisted intent
  owned by ProjectState. Calculated duty is not saved as engineering authority.
- `HVAC/dev/test_hs73a_pump_duty_preview_v1.py`: numerical, invalidation,
  persistence and real-widget integration checks.

Legacy pump sizing/selection engines remain unchanged. Their default allowances
and efficiency are not used by H-S73-A. Manufacturer selection remains optional
even for a later completed parameter-based design including Kv/Kvs.

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
