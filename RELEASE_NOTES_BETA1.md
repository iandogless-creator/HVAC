# HVACgooee Beta 1 — 0.6.0b1

Status: release preparation, not yet tagged or published.
Baseline: phase-hydronics-h-a at 53f424d, plus the reviewed local pump,
shared-water and Kvs editor work collected on 8 October 2026.

## Changes for beta users

- Explicit New/Open/Sample startup; developer sample is no longer automatic.
- Pinned Python GUI dependency and a simple source launcher.
- Project folder defaults under Documents/HVACgooee, independent of the source
  installation. Existing project locations and saved engineering values persist.
- GPLv3 licence text, current feature documentation and a curated source archive
  builder with exact file hashes and a selected regression runner.

## Accepted recent work

Topology Wizard and Education were committed/pushed as 53f424d. Ian confirmed
Kvs row contrast (H-S73-C1) and per-point unfinished-choice preservation
(H-S73-C2) working in the real workspace. Pump duty and shared water-property
paths are included in the reviewed source, with existing explicit acceptance
and stale-basis gates. A user's project-duty acceptance is separate from software
release acceptance.

## Known limitations

- Source distribution for Linux Mint/Ubuntu and Python 3.12; standalone
  installers, Windows and macOS are not validated for this beta.
- No autosave or comprehensive unsaved-change warning; save before New/Open/Quit.
- Existing generated room-list topology and demonstration defaults require review.
- Pure-water temperature range and reference-pressure limits are in README.md.
- Pump/valve products and manufacturer performance verification remain optional
  separate work. No automatic whole-system design approval or balancing settings.
- Beta wording, Education content and developer-facing controls can be refined.
- Historical/parked modules are not an alternative supported entry point. The
  archive follows the active GUI and selected-test import closure. Unused older
  serializers and a legacy ventilation module have pre-existing syntax errors
  and remain outside that archive. The active project_v3 checksum persistence
  and V4 heat-loss paths are tested; all historical repository files are preserved.
- The selected regression suite is not a claim that every historical dev script
  passes, or that every engineering workflow has independent external validation.

## Release gate

Before public publication: run tools/verify_beta1.py locally, inspect native
startup/New/Open/Sample and save/reopen on Ian's desktop, review the exact scoped
Git diff, commit the accepted source and documentation, build the curated source
archive, then tag that verified commit and publish a prerelease. Record the tag,
commit, checksums and local test results in CURRENT_STATE.md.

No tag, push, public upload or design acceptance is performed by this preparation.
