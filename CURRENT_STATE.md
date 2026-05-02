# HVACgooee — Current State

Status: ACTIVE DEVELOPMENT
Current branch: `phase-iv-b-adjacency`
Current working phase: Phase V-C — Construction Authority + Vertical Adjacency

## What is current?

The current working system is:

- `HVAC/gui_v3/`
- `HVAC/dev/bootstrap_dev_project.py`
- `HVAC/dev/bootstrap_registry.py`
- `HVAC/dev/bootstrap_vertical_3room.py`
- `HVAC/dev/dev_constructions.py`
- `HVAC/fabric/generate_fabric_from_topology.py`
- `HVAC/heatloss/fabric/row_builder_v1.py`
- `HVAC/topology/`
- `HVAC/project/project_state.py`

The current GUI entry point is:

```bash
python HVAC/gui_v3/run_gui_v3.py

Current capability

The current GUI v3 can:

load DEV scenarios from the DEV mode selector
switch between simple and vertical-stack DEV states
display heat-loss rows without exposing construction IDs
resolve U-values from ProjectState.constructions
display adjacency in the Element column, e.g. Wall → Middle
open adjacency editing from the ΔT column
commit adjacency changes back into ProjectState.boundary_segments
refresh ΔT, Qf, and room totals live
Current authority rules
ProjectState is the sole engineering authority.
Panels are observer-only.
GUI panels emit intent only.
Construction IDs remain internal.
U-values come from constructions only.
Boundary segments own adjacency.
Heat-loss rows are projections, not authority.
Known current limitations
Vertical-stack DEV wall/internal partition rows still need area cleanup.
Some debug prints remain intentionally during stabilisation.
Hydronics is not yet the active development target.
Persistence is present but not the current focus.
Historical docs may be stale unless referenced from this file.
Current recommended next work
Clean vertical-stack segment area validation.
Improve adjacency panel room-name display.
Standardise construction IDs fully on DEV-EXT-WALL, DEV-INT-WALL, etc.
Remove old debug prints once adjacency/area behaviour is frozen.
Then move toward hydronics integration.
