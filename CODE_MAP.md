# HVACgooee — Code Map


## B1-A Beta 1 source release

- `run_hvacgooee.py` / `HVAC/gui_v3/run_gui_v3.py`: explicit startup choice, retained
  code-painted splash, GUI event loop and application identity from `HVAC/version.py`.
- `startup_project_dialog_v1.py`: New/Open/Sample/Quit chooser; no calculations.
- `startup_projects_v1.py`: shared existing New/Open project preparation used by
  startup and MainWindow. Existing acceptance/commit authority is unchanged.
- `gui_project_context.py`: user Documents/HVACgooee default folder; Open/Save As
  use this location without moving existing projects or preferences.
- `requirements-beta1.txt`, `LICENSE`, `README.md`, `RELEASE_NOTES_BETA1.md`:
  dependency, licence and release-facing documentation.
- `release/beta1-files.json`, `tools/build_beta1_source.py`: explicit source scope,
  committed-source gate, candidate option and archive/file checksums.
- `tools/verify_beta1.py`: selected isolated regression gate. New startup/entrypoint
  tests exercise Qt actions, shared lifecycle and real event-loop startup paths.


## H-S73-C2 Kvs editor session drafts

- `hydronics_schematic_panel.py`: per-point candidate/consequence drafts,
  evidence-bound reuse, explicit Clear and project-session reset. C1 retains
  dark text on the pale-orange Kvs evidence focus row.
- `hydronics_schematic_panel_adapter.py`: supplies existing exact duty and
  consequence fingerprints in editor rows; binds the project before refreshing.
  Existing engineering Accept/Apply/Clear paths remain authoritative.
- `test_hs73c2_kvs_editor_drafts_v1.py`: real Qt point switches and refreshes,
  precision changes, draft expiry, explicit actions and adapter project scope.

## H-S73-C active shared water basis

- `HVAC/fluid/water_properties_v1.py`: pure IAPWS density/viscosity runner,
  immutable mean-flow/return basis, strict persistence and stale comparison.
- Basic PS and common-main sizing, route/main Colebrook, Local K and RR added
  length explicitly resolve this pair; low-level historical defaults remain
  for standalone compatibility only.
- `route_pressure_accumulator_v1.py` →
  `committed_proportioning_hydraulic_input_authority_v1.py`: numeric evidence
  and its water provenance travel together; snapshot builder checks current
  inputs before returning an explicitly committable snapshot.
- Required Kv and accepted-Kvs consequence modules use liquid specific gravity.
  Adapter passes live fluid identity into existing point-duty fingerprints.
- Pipe sizing/resizing projections carry frozen water provenance; schedule
  fingerprint and rebuild preserve it. Live commit rejects stale temperatures.
- Pump controller validates current versus frozen water basis, inherits exact
  density and blocks legacy/stale duty. Widget rounds display only, preserving
  exact payload and ordinary allowance drafts. No automatic saved-basis write.
- Environment panel displays the adapter-resolved basis; Environment changes
  notify Hydronics, Basic and Local K. Derived properties are not GUI authority.
- `test_hs73c_shared_water_properties_v1.py`: published numerical references,
  actual route/Local K/RR/resize consistency, Kv inverse, legacy/corrupt loading,
  explicit commit guard, exact-basis staleness and transactional resize handoff.
- `test_hs73c_shared_water_gui_v1.py`: real Environment inputs, Pump refresh,
  invalid/stale gates and preservation of frozen engineering records.

The B2 fixed-density/manual-override path below describes the earlier stage;
H-S73-C supersedes it in the current active hydraulic path.

This file identifies the current active code path.

For current project status, see `CURRENT_STATE.md`.

## H-S73-B2 Pump density draft and concise guidance

- `pump_preview_controller_v1.pump_preview_draft_defaults_v1`: read-only editor
  suggestions from the existing pipe hydraulic water-density constant for a
  supported basis-only snapshot; zero extra loss/margin. No saved intent write.
- Hydronics adapter supplies the draft separately from the saved Pump basis.
- Pump preview widget restores saved values, preserves ordinary-refresh drafts,
  shows the density source and removes the automatic note on a density edit.
- Pump explanations are shortened; detailed loss and Kv boundaries remain in
  hover help. Apply and Accept remain separate explicit controller actions.
- `HVAC/dev/test_hs73b2_pump_density_defaults_v1.py`: density source, zero drafts,
  explicit Apply, saved values, manual overrides and project lifecycle.

## H-S73-B1 Pump frozen route identity compatibility

- `HVAC/hydronics/pumps/pump_preview_controller_v1.py`: read-only matching of
  frozen leg:subleg section membership to explicit committed route IDs;
  preserves unique first-common-main, positive-flow and exact-coverage gates.
- `HVAC/dev/test_hs73b1_pump_route_identity_v1.py`: exact/qualified membership,
  missing/duplicate/ambiguous rejection, flow gate and stale-basis regression;
  optional read-only saved-project check through the production snapshot loader.

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

## H-S73-B required design-duty path

- `HVAC/gui_v3/widgets/pump_duty_widget_v1.py`: route equipment/Kv inputs,
  controller-result display and explicit Apply/Accept/Withdraw/Clear intents.
- `HydronicsSchematicPanel`: Pump sub-tabs Preliminary and Duty.
- `HydronicsSchematicPanelAdapter`: wires intents, refreshes after explicit
  writes and project swaps, preserves unfinished editor inputs on refresh.
- `HVAC/hydronics/pumps/pump_duty_controller_v1.py`: joins committed routes and
  valve points, validates coverage/Kv/review, constructs the loss ledger and
  owns acceptance. `preview_pump_duty_v1().accepted` validates saved authority.
- `HVAC/hydronics/pumps/pump_duty_runner_v1.py`: pure liquid Kv pressure loss;
  reuses `pump_preview_runner_v1.py` for flow, common-loss/head reserve and head.
- `HVAC/hydronics/pumps/pump_duty_basis_v1.py`: optional persisted route/Kv
  intent and separately fingerprinted required-duty acceptance.
- `ProjectState`: compatible optional `hydronic_pump_duty_basis` and
  `hydronic_pump_duty_acceptance` save/load; absent fields remain unset.
- `HVAC/dev/test_hs73b_pump_duty_v1.py`: independent arithmetic, shared valves,
  controlling-route change, invalid input, explicit acceptance and checksummed
  persistence/stale rejection.
- `HVAC/dev/test_hs73b_pump_duty_gui_v1.py`: real panel/adapter actions, draft
  preservation, project swap and invalidated acceptance display.

This path accepts the required design duty without selecting a pump. Existing
balancing allocations are reference only and are not added to Kv losses.

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
