# HVACgooee — Current State

Status: ACTIVE DEVELOPMENT  
Current branch: `phase-hydronics-h-a`  
Current working area: Hydronics Phase H — Proportioning / return-arrangement evidence  
Last updated: 2026-07-05

---

## What is current?

The current active system is Hydronics GUI v3 and the Hydronics proportioning preview path.

Main working files include:

- `HVAC/gui_v3/panels/hydronics_schematic_panel.py`
- `HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py`
- `HVAC/gui_v3/widgets/common_main_leg_subleg_schematic_widget_v1.py`
- `HVAC/hydronics/proportioning/`
- `HVAC/hydronics/sizing/`
- `HVAC/hydronics/local_losses/`
- `HVAC/hydronics/pipes/dp/`
- `HVAC/core/fluid_friction/`
- `HVAC/core/materials/pipe_materials_library.py`

The current GUI entry point is:

```bash
python HVAC/gui_v3/run_gui_v3.py
```

---

## Current capability

The current Hydronics / Proportioning work can:

- Display room / emitter demand evidence.
- Build branch-aware Basic PS section rows.
- Show carried flow per section.
- Show pipe size, velocity, Δp/m, Reynolds number, friction factor, method, and iteration count.
- Use a shared Haaland / Colebrook friction core.
- Use Colebrook-backed route pressure evidence after Basic PS handoff.
- Show Local K pressure preview per section.
- Show straight Δp, local Δp, and section Δp.
- Rank route Δp candidates.
- Identify controlling route candidates.
- Show route shortfall / preliminary balancing burden evidence.
- Compare F&R and F+RR return paths.
- Show reverse-return added length evidence.
- Support RR length basis modes:
  - Physical loop — no extra allowance
  - Downstream proxy allowance
  - Manual allowance
- Allow user acceptance of return arrangement basis at:
  - system level
  - leg level
  - common subleg level
  - branch subleg level
- Show chosen-basis route pressure evidence in the Proportioned tab.
- Commit a frozen proportioning-basis snapshot.

---

## Current authority rules

ProjectState remains the sole engineering state authority.

Panels are observer / intent-emitter UI.

Hydronics preview rows are engineering evidence, not final hydraulic output.

Return arrangement acceptance is user design intent.

Basic PS remains a first-pass sizing / handoff basis.

Colebrook-backed route pressure is detailed pressure evidence after handoff.

The current Hydronics work does **not** yet perform:

- pump selection
- valve selection
- final balancing
- pipe resizing
- final hydraulic result generation
- automatic design choice from F&R / F+RR comparison evidence

---

## Current Hydronics position

Recently completed / active milestone chain:

- H-S29-A — shared Haaland / Colebrook friction core
- H-S29-B — hydronics Colebrook compatibility wrapper
- H-S29-C — hydronics mass-flow pressure wrapper
- H-S29-D — Basic PS friction helpers call shared core
- H-S29-E — route / section pressure projection uses hydronic mass-flow wrapper
- H-S29-F — expose route / section friction metadata
- H-S29-G — merge route accumulator Colebrook metadata into received section rows
- H-S29-I — apply RR added length to F+RR route comparison
- H-S29-J — show RR added-length evidence in return comparison rows
- H-S29-K — RR added-length basis mode
- H-S29-L — expose RR length basis in return arrangement acceptance
- H-S29-M — RR length basis mode control
- H-S29-M1 — store RR length basis mode in return arrangement intent
- H-S29-M2 — refresh return acceptance evidence after F&R / F+RR basis change
- H-S29-N — next: manual RR extra length entry

---

## Current known transition debt

Some Hydronics behaviour currently lives in adapter / panel wiring while the Hydronics controller boundary is still maturing.

This is accepted short-term Hydronics transition debt.

It must not be interpreted as a permanent relaxation of the architecture freezes.

Longer term, user intent and commits should move behind explicit controller paths where appropriate.

Before final hydronic output, pump selection, valve selection, final balancing, or pipe resizing become authoritative, those commit paths should be reviewed and moved behind explicit controller boundaries.

---

## Current local caution

Do not remove local project folders, notes, or backup files unless explicitly requested.

Known local material may include:

- `HVAC/HVACprojects/20 room multileg/`
- `HVAC/HVACprojects/6 room/`
- `HVAC/HVACprojects/9 room/`
- hydronics notes
- local `.bak_hs*` backup files
- local schematic widget work

These are normal working material.

---

## Current recommended next work

Immediate:

1. Finish / commit H-S29-M1 and H-S29-M2 repair if not already committed.
2. Continue H-S29-N — manual RR extra length entry.
3. Confirm Manual allowance mode enables metre entry and updates RR extra Δp evidence.
4. Keep evidence as guidance only; user design basis remains authoritative.

Next after H-S29-N:

- tidy RR length basis persistence and project save / load behaviour if needed
- add clearer return-arrangement note: “Evidence is guidance only — user design basis remains authoritative”
- review Hydronics controller boundary debt
- continue toward final proportioning output preview

---

## Current status note

Heat-Loss, construction assignment, wall wizard, and opening schedules remain important.

They are not the current active development focus.

Hydronics proportioning evidence is the current active focus.
