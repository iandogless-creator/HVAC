# HVACgooee — Beta 1

HVACgooee is Ian Allison's open-source, deterministic HVAC calculation and
education application. This release candidate is **0.6.0b1**, following the
repository's earlier v0.5 development milestone. The core is GPLv3.

## Install and start

Beta 1 targets Linux Mint / Ubuntu with Python 3.12 and PySide6 6.10.1.
Download and extract the curated Beta 1 source archive, then open a terminal
in its folder:

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-beta1.txt
.venv/bin/python run_hvacgooee.py
```

Use Python 3.12 for this beta. If your system lacks the venv module, install
its Python venv package using your distribution's package manager. Initial
installation needs access to PyPI; the application does not require an account
or an AI service. This source release contains the active GUI, its imported modules and the selected
release tests. Historical/parked code stays in the repository. It is not a
standalone desktop installer.
Windows and macOS have not been validated for Beta 1.

The startup chooser offers **New project**, **Open project** and **Sample
project**. Open selects a folder containing `project.json`. Sample opens a fresh unsaved copy of **HVACgooee — 20-room example**, based
on the existing 20-room multi-leg job. It retains the example design inputs and
saved engineering records; normal stale-basis checks still apply. Save asks for
your own copy folder. The bundled example and existing user jobs are untouched.
Sample opens in the existing floating **Heat Loss** view, with Navigation visible.
Saved Heat Loss panel positions and Navigation placement are reused; New/Open
continue to restore the usual last-selected view. No calculation runs automatically.
All 80 wall segments in this example are currently external; room-to-room
adjacency is not defined. Review the layout and inputs before treating its
heat-loss or hydraulic results as a design.
New first opens the existing folder chooser at `HVAC/HVACprojects` inside the
installation. Use **New Folder**, name the job, then select that empty folder.
The job name comes from the folder, and the existing checksummed saver writes
its initial `project.json` before opening the single-room workspace. Cancel
leaves the current project/startup chooser in place; non-empty folders are refused.

New/Open/Save As default to that same `HVAC/HVACprojects` root; you can browse
to another location. The installation must be writable for its default job folder.
Existing project folders remain usable wherever they are stored. Save As selects
the final project folder. Save explicitly before closing or switching projects:
there is no autosave or comprehensive unsaved-change prompt in this beta.
For beta evaluation, work with copies of important projects.

## Included workflows

- Rooms, constructions, U-values, openings and committed heat-loss display.
- Topology Arranger with optional Wizard and contextual Education.
- Hydronic pipe, Local K and flow/return or reverse-return evidence.
- Explicit hydraulic-basis and pipe-schedule commits where their gates pass.
- Generic Kv/Kvs evidence, explicit point acceptance and consequence review.
- Preliminary pump duty and parameter-based required duty with route equipment
  losses, operating Kv, explicit allowances and separate duty acceptance.
- Temperature-dependent pure-water density and viscosity, using the mean
  Environment design flow/return temperature.
- Named workspace views, Navigation, Light/Dark appearance and per-point Kvs
  editor drafts that survive unchanged refreshes within the current session.

A manufacturer product is optional for parameter-based required-duty work.
Accepting required duty does not select or verify a physical pump, valve,
manufacturer curve, NPSH performance or installation suitability.

## Engineering and beta limits

Previews remain evidence. Accept/Commit actions retain their existing exact-basis
checks. Changing source inputs can invalidate previous acceptance; displayed
values or stored acceptance fields alone do not establish current readiness.
No beta startup action automatically accepts a hydraulic design or pump duty.

Water-property support is pure water, design flow and return each 5–95°C, with
flow above return, at a 0.1 MPa reference. Ambient air temperature is not used
as the water temperature. Glycol and pressure-dependent corrections are outside
this stage. Existing heat-capacity/mass-flow conventions remain unchanged.

Legacy room-list topology seeding remains in the existing adapter path; always
review generated routing against the intended installation. Some optional
catalogue content is demonstration evidence, not a manufacturer endorsement.
The developer panel and some engineering wording remain visible in this beta.
Unsubmitted editor drafts are session-only and are not saved in projects.

See [RELEASE_NOTES_BETA1.md](RELEASE_NOTES_BETA1.md), [CAVEATS.md](CAVEATS.md)
and [CURRENT_STATE.md](CURRENT_STATE.md) for the verified checkpoint and limits.

## Verify and report a problem

From the extracted source folder, with the same environment:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python tools/verify_beta1.py
```

This runs the selected release checks in isolated temporary user settings and
project folders. It does not modify your saved projects. Native-window testing
on the target desktop is still part of release acceptance.

Report the version (`.venv/bin/python run_hvacgooee.py --version`), operating
system, steps taken, expected result, actual result and relevant terminal output.
A screenshot and a small anonymised example help. Do not attach private projects
or credentials. Issue tracker: https://github.com/iandogless-creator/HVAC/issues

## Architecture and licence

ProjectState owns engineering intent and committed state. Controllers own
execution/acceptance policy; deterministic engines calculate; adapters project;
GUI panels display evidence and emit user intent. No proprietary AI is required
by the core.

The core is licensed under the GNU General Public License version 3. See
[LICENSE](LICENSE). PySide6/Qt is installed separately and retains its own
licensing and notices. Historical notes and unrelated project data are not part
of the curated release archive.

Authority documents: `CURRENT_STATE.md` → `CODE_MAP.md` →
`ARCHITECTURE_FREEZES.md` → `FREEZE_INDEX.md`.

Author: Ian Allison.
