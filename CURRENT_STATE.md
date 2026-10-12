# HVACgooee — Current State

## B1-B/C/D locally verified — release checkpoint — 12 October 2026

Ian's terminal confirms 21/21 selected Beta 1 checks passed, including job folders,
the 20-room sample, its opening view, startup, save/reopen, navigation, topology,
pump duty, shared water properties and Kvs drafts. git diff --check is clean.
Ian accepted the native opening layout ("all seems tidy"); screenshots show Rooms,
Heat Loss, Geometry, ACH, Environment, Education and Navigation populated.
Automated save/reopen passed; a manual close/reopen is not inferred from screenshots.

Git evidence: branch phase-hydronics-h-a, local HEAD 6dcbfb4 (Prepare HVACgooee
Beta 1 with reviewed hydronics and startup); origin/phase-hydronics-h-a remains
53f424d in the supplied output. The staging area was empty. B1-B/C/D are applied
but still uncommitted at this checkpoint. This refreshed scope contains 20 files,
including the bundled sample under HVAC/examples, and supersedes the old B1-A
staging helper. No push, tag, final archive build or publication is yet verified.

New/Open use the shared installation-relative HVAC/HVACprojects root. New creates
and saves a job in an explicitly selected empty folder through existing project
routines. Sample loads an independent copy of the supplied 20-room design, named
HVACgooee — 20-room example, and opens the existing floating Heat Loss view.
Save As previously confirmed a separate Sample/project.json. Adjacency remains
undefined in the supplied sample; pipe topology does not establish room geometry.

The two reported deletions under HVAC/HVACprojects (clean_4_room_identity_test and
example) are outside this checkpoint. Their cause is unverified; the staging
helper neither stages nor restores them. Existing jobs, old/ folders, notes,
numeric files, H-S29 tests, backups and other unrelated work remain untouched.
Engineering acceptance remains explicit and project-specific; GPLv3 is unchanged.

Next: review and commit this scoped checkpoint, build the curated source archive
from the committed release files, and record its checksum before Beta 1 release.
Earlier prepared sections below are historical; this entry supersedes their
pending local-test, native-layout and Git-head statements.


## B1-D prepared — Sample opens in Heat Loss view — 11 October 2026

Ian's screenshot requests a useful initial sample workspace with Rooms, Heat-Loss,
Environment and Navigation. The startup Sample action now selects the existing
floating Heat Loss view once, after window construction and before normal use.
It reuses the saved named view and its panel positions (or existing default
placement when absent). Navigation is shown at its independently restored
placement. The existing Geometry/ACH companion panels follow that same view.
No new layout schema, fixed screen coordinates or copied desktop preferences.

New/Open keep ordinary last-view restoration. Later Navigation/view choices remain
available and persist normally; the startup override is consumed once. No automatic
heat-loss run, project write or engineering acceptance is added.

Verified locally by Ian on 10 October: B1-B applied with 19/19 checks, then B1-C
applied with 20/20 checks. His Open screenshot shows HVAC/HVACprojects with the
existing jobs intact. The 11 October screenshot confirms Save As wrote the sample
copy to HVAC/HVACprojects/Sample/project.json. Manual reopen confirmation and latest
Git commit/staging state remain pending; no release publication is asserted.

B1-D validation in the prepared source: actual startup Sample route, existing
New/Open restoration, saved view/Navigation placement, visible default panels,
one-shot presentation and unchanged project data; selected Beta 1 regressions,
compilation, archive membership and guarded patch checks. Native appearance remains
for Ian to review. Next: inspect Sample startup, confirm reopen and Git status,
then prepare the refreshed scoped Beta 1 commit and archive.


## B1-C prepared — bundled 20-room sample — 10 October 2026

Ian confirmed New/Open should start at HVAC/HVACprojects and requested the
existing 20-room example for Sample. B1-B supplies the shared job-folder default.
B1-C replaces only the startup sample action with a bundled copy of the supplied
4 October project.json, named "HVACgooee — 20-room example". Room IDs, branch
labels, dimensions, construction inputs, topology and stored engineering records
are preserved. Only the bundled project name/identity and checksum are changed.
Every Sample invocation loads through the existing checksum validator, gives the
copy a new project ID and clears its filesystem binding. Save therefore invokes
Save As; no existing user job or bundled file is written on sample opening.

The supplied example has 20 rooms on Ground Floor and 80 external wall segments,
with no recorded room-to-room adjacency. Pipe branch membership does not imply
shared walls. Adjacency refinement requires an explicit sample room layout and
subsequent recalculation/review; this patch does not invent one or grant new
engineering acceptance. Existing stale-authority checks remain in force.

Validation in the prepared source: sample count/name/identity, preserved design
records, fresh copies, original-file preservation, checksum rejection, Save As
and reopen, real startup processes, plus the selected Beta 1 suite. The sample
JSON is included explicitly in the release manifest. Native B1-B/B1-C acceptance,
latest local commit/build state and refreshed scoped staging remain unconfirmed.
Next: inspect the 20-room sample and save/reopen a separate copy; obtain current
Git status before committing or rebuilding the Beta 1 release archive.


## B1-B prepared — established job root and explicit New folder — 9 October 2026

Ian requested the existing HVAC/HVACprojects location shown in his screenshot
instead of B1-A's Documents default. The shared default is now resolved relative
to the installed HVAC package, independent of the shell's working directory.
Startup Open and main-window Open/Save As use that same root.

New at startup and File > New reuse the Qt folder chooser and existing project_v3
checksummed saver. Create a job folder with New Folder, then select that empty
folder. Its name becomes the job name; the initial project.json is saved before
binding the workspace. Cancel keeps the current project or startup chooser.
Selecting the job-root itself or a non-empty folder is refused, preserving old
jobs and notes. Sample remains an unsaved example. Existing Save As semantics
and all engineering calculations/acceptance boundaries remain unchanged.

The 8 October 63-file stage was verified in Ian's output; whether the subsequent
commit/build commands ran is unconfirmed. This patch changes working files only:
its updated files must be included in a refreshed scoped commit before a release
archive is built. The previous staging helper expects B1-A bytes and is superseded.
Prior native save/close/reopen confirmation remains pending for this new flow.

Validation in the prepared source: focused folder/save/reopen, cancellation,
existing-job preservation, write-failure handling and real startup/menu wiring;
selected Beta 1 regression suite, compilation and guarded installer checks.
No user project files, Git staging, tags or engineering acceptances are changed
by applying the patch. Next: native New Folder/save/reopen, then verify Git status
and prepare the updated commit/release checkpoint.


## B1-A locally verified — scoped commit preparation — 8 October 2026

Ian applied the 20-file B1-A patch with guarded backups. His terminal confirms
18/18 selected Beta 1 checks passed and git diff --check produced no output.
The native startup chooser shows Beta 1 (0.6.0b1), with New/Open/Sample/Quit.
Ian identified the Hydronics screenshot as the Sample project: Undecided return
arrangement and its explicit commit blocker do not establish a loading defect.
Ian confirmed the new-project location under Documents; the configured default
is ~/Documents/HVACgooee. Manual save/close/reopen confirmation is still pending.
Automated save/reopen and entry-point checks passed; these are distinct evidence.

Git output on 8 October confirms branch phase-hydronics-h-a, HEAD and origin at
53f424d, with an empty staging area before this preparation. The scoped staging
helper includes the reviewed H-S73-B/B1/B2/C/C1/C2 work and B1-A preparation,
including explicitly named release tools/dependency files even if ignored.
It preserves unrelated projects, notes, H-S29 tests, numeric files and backups.
No tag, push, publication or project-specific engineering acceptance is implied.

The local 18-test result now also verifies the previously pending H-S73-C shared
water and H-S73-C2 draft regression suites. Earlier sections below describe their
historical delivery checkpoints; this section supersedes their pending test steps.

Next: confirm manual save/close/reopen, review the scoped staged diff and commit.
Then build the curated archive from that commit, record its checksum and prepare
the v0.6.0b1 prerelease. Final pump duty remains an explicit project design action.



## B1-A prepared — Beta 1 release candidate — 8 October 2026

Ian requested HVACgooee Beta 1 after accepting H-S73-C2. The collected working
source is verified by SHA-256 against its manifest: all 47 compared files match
prior deliveries. Actual repository HEAD/origin remains 53f424d on
phase-hydronics-h-a, with no staged changes in the supplied terminal output.
The later pump/shared-water/Kvs changes remain local pending a scoped commit.

Beta identity: 0.6.0b1, following the earlier v0.5 development milestone.
This is preparation, not a published release or a Git tag.

- Startup explicitly offers New/Open/Sample/Quit before constructing the workspace.
  The developer sample is used only after Sample. Existing New/Open project
  preparation is shared; existing engineering calculations and acceptance paths
  are retained. Invalid opens report an error; cancelling does not start a sample.
- User project folder defaults move from source/current-working-directory paths
  to ~/Documents/HVACgooee. Open/Save As can still use existing folders elsewhere.
  Existing project data and workspace preference files are not migrated or removed.
- Added source launcher, pinned PySide6 6.10.1 dependency, GPLv3 licence text,
  updated README and Beta 1 release notes. Python 3.12/Linux Mint/Ubuntu is the
  initial target; standalone installers and other OSes remain outside this beta.
- Added explicit release-file manifest, source builder with per-file hashes and
  SHA-256 output, and selected regression runner with isolated settings. A final
  source archive requires all listed release files committed; unrelated files may
  remain modified/untracked. Candidate mode labels an uncommitted review archive.
- The archive follows the active GUI/test static import closure. Pre-existing
  syntax errors in unused serializers and an older ventilation module remain
  preserved in the repository, outside this supported release path. Existing H-S29 untracked
  tests, saved projects, notes, numeric files and backups remain outside scope.

Validation in the supplied source copy: fresh Python 3.12 environment with only
PySide6 6.10.1; selected startup, independently checked starter heat-loss arithmetic and save/reopen,
heat-loss wizard lifecycle, Navigation,
Topology, pump, shared-water and Kvs draft checks; actual New/Open/Sample/Cancel
entry-point processes; source-archive compilation and extracted-archive checks.
Offscreen verification supplements, but does not replace, Ian's native GUI review.
No user project or engineering acceptance was written by release preparation.

Next: apply the guarded B1-A patch, run tools/verify_beta1.py in Ian's environment,
inspect the native startup chooser and save/reopen workflow, then record the local
results and prepare the exact scoped commit. Build from that commit before tagging
and publishing a prerelease. Final duty acceptance remains project-specific.


## H-S73-C2 runtime accepted — 8 October 2026

Ian requested preservation of unfinished Kvs and consequence choices while
switching balancing points or refreshing unchanged evidence. C1 row contrast
is visually accepted. C2 is prepared against the delivered C1 source copy;
Ian confirmed application and working behaviour on 8 October 2026.
Separate local test output was not supplied; source hashes match the delivered patch.

- The panel retains candidate and consequence dropdown choices per stable point
  for this project session, including an intentionally unselected placeholder.
  Point switching, reordered rows and unchanged refreshes do not submit them.
  Status text distinguishes an unsubmitted choice from the saved acceptance.
- Adapter-provided exact duty/consequence fingerprints protect draft reuse;
  rounded display values are not used as proof of unchanged evidence.
  Changed/missing evidence, removed points or a different project object discard
  affected drafts. Returning to old evidence does not revive a discarded draft.
- A changed saved Kvs acceptance invalidates its draft and dependent consequence
  draft. A consequence-only change preserves the independent candidate draft.
  Explicit Clear discards that field's draft. Accept/Apply still use the existing
  adapter/controller paths; an unsuccessful action with unchanged evidence keeps
  its unfinished selection. No automatic Kvs selection or engineering acceptance.
- Drafts are GUI memory only, not saved project values or restart preferences.
  No schema, fluid calculation, engineering authority or GPLv3 boundary change.

Validation in the prepared source copy: real Qt draft lifecycle suite, exact
precision changes, explicit action payloads, project rebinding, nearby Kvs
acceptance/disposition and focus regressions, compilation and guarded installer
checks. These checks do not assert that Ian's repository tests have run.
Last verified push remains 53f424d; final pump duty remains unaccepted.

Next: apply C2, run test_hs73c2_kvs_editor_drafts_v1.py, and inspect switching
between two Kvs points with unfinished selections. No commit or push is included.
Preserve unrelated projects, notes, backups and repository work.


## H-S73-C1 visually accepted — 6 October 2026

Ian's screenshot shows pale text on the pale-orange balancing-point focus row
in Dark mode. Values remain present; this is a display contrast defect.
The focused evidence row now uses dark text, and both foreground/background
return to theme defaults when focus moves or clears. No calculations, Kvs
choices, acceptance, ProjectState, saved projects or Git state are changed.

H-S73-C is visible in Ian's Environment screenshot (75/65°C, mean 70°C,
977.764 kg/m3, 0.4035 mPa.s). Local C terminal test results and a newer Git
checkpoint have not been supplied. Last verified push remains 53f424d;
final duty remains unaccepted. Stale approvals still require explicit review.

Validation in the supplied source copy: focused Light/Dark widget checks for
row switching, refresh and clearing; existing linked-Kvs-focus regression;
compilation, visual review and guarded installer checks. Ian confirmed the real workspace is visually OK on 6 October 2026. The separately reproduced unfinished-dropdown
reset remains open and is not part of this contrast patch.

Next: apply C1 and inspect Kvs Design while changing the balancing point.
Highlighted text should remain legible, with the former row returning to its
normal theme colours. Preserve unrelated work, notes, projects and backups.

## H-S73-C prepared — shared hydraulic water properties — 4 October 2026

Prepared against Ian's full fluid-source archive. It contains H-S73-B2, so B2
application is now confirmed from source; Ian's B2 runtime acceptance was not
reported. H-S74-A remains accepted/pushed as 53f424d. H-S73-B/B1/B2 remain
local at the last verified Git checkpoint; final duty remains unaccepted.
This patch makes no Git changes and asserts no newer local branch/status.

- Pure-water density and dynamic viscosity now share IAPWS SR6-08(2011)
  equations (2)/(7), evaluated at mean Environment design flow/return.
  The pressure reference is 0.1 MPa, not a fill-pressure assessment. The
  project requires both inputs within 5–95°C and flow above return. Missing,
  invalid, non-finite and unsupported recorded property bases fail closed.
  Ambient air temperature is not a water-property input. At 75/65°C the
  mean is 70°C: 977.764008 kg/m3 and 0.0004035454265 Pa.s.
- Live Basic PS, common-main/leg-entry, route friction, Local K and RR
  added-length evidence use the same density/viscosity pair. Environment
  changes refresh Hydronics, Basic and Local K observers.
- Required Kv and accepted-Kvs pressure consequences now include liquid
  specific gravity (rho/1000), consistent with H-S73-B operating-Kv losses.
  The existing point-duty fingerprint includes property provenance, so
  changed evidence requires fresh explicit Kvs/consequence review.
- Route evidence carries an immutable water basis into typed committed
  hydraulic authority. Optional nested persistence stores both temperatures,
  mean, model, reference pressure, density and viscosity. Old snapshots load
  without being rewritten or silently assigned modern fluid authority.
- Pump needs a current committed water basis. Legacy snapshots require review
  and explicit Recommit Proportioning. Temperature changes (including a
  changed difference at the same mean) block preview/duty acceptance without
  deleting saved snapshots, inputs or acceptance records. Returning to the
  exact accepted basis may resolve existing exact-basis acceptance again.
- Resizing uses frozen properties, carries them through the accepted schedule
  fingerprint and rebuilt snapshot, and blocks a commit against changed live
  temperatures. Existing low-level legacy resize APIs remain compatible;
  the live GUI explicitly requires the new fluid basis.
- Environment displays the derived basis. Pump density is inherited/read-only,
  rounded only for display; Apply sends the full-precision value. Zero extra
  common loss/head margin drafts and unfinished allowance edits are preserved.
  Apply and final Accept duty remain separate explicit actions.

This supersedes B2's fixed-water/manual-density proposal for active project
hydraulics. Existing heat capacity and mass-flow input conventions are retained.
No glycol, pressure-dependent property correction, pump product/curve selection,
NPSH assessment, automatic pipe-schedule commit or automatic duty acceptance.
The older standalone fluid library is outside this active Phase H path.

Validation in the supplied source copy: seven H-S73-C engineering checks,
real Environment/Pump signal and stale-state GUI checks; H-S73-A/B/B GUI,
B1 and updated B2; required-Kv/inverse-Kvs, main/route material identity,
commit handoff and resize regressions; H-S74-A contextual-help regression.
Changed Python files compile. Guarded installer and whitespace checks are
verified before delivery. Offscreen 16:9 visual review found and corrected
Environment label clipping. The archive omits an optional valve-catalogue JSON;
its unavailable message and deliberately incomplete fixture topology warnings
do not fail these tests. No manufacturer data was invented. Repository-wide
compilation also exposes pre-existing syntax errors in unrelated legacy files;
those are preserved. Ian's real-project validation remains pending.

Next: apply the guarded H-S73-C patch, run both H-S73-C suites, inspect
Environment and recalculated hydraulic/Kv evidence, explicitly review affected
approvals and Recommit Proportioning, then Apply the inherited Pump basis.
Final Accept duty remains the designer's separate action. Keep all projects,
notes, backups and unrelated work. Do not commit/push this stage until accepted.

## H-S73-B2 prepared — Pump density and wording — 4 October 2026

H-S73-B1 is locally verified: all four requested suites passed (the four-test
B1 suite plus H-S73-A, H-S73-B and B GUI); git diff --check was clean. Ian's
real-project screenshot shows 0.349282 kg/s from the first common main, all
four routes and the expected 68089 Pa chosen-route maximum. The false route
coverage blocker is resolved. This supersedes earlier B1 pending notes below.

Ian authorised inherited density, shorter explanations and zero defaults for
additional common loss/head margin. Source inspection confirms that the current
basis-only pipe, Basic PS and Local K paths use fixed water density 998 kg/m3;
Environment's flow/return temperatures do not resolve temperature-dependent
density in these paths. This stage does not introduce new fluid physics.

- New supported basis-only Pump drafts read WATER_DENSITY_KG_M3 from the pipe
  pressure module and display a fixed-water source note, not temperature-
  corrected density. Missing/invalid and resized snapshot density is not guessed.
- Extra common loss and head margin start at 0 in the editor. No project intent
  is written until Apply basis. Existing saved density, allowances and notes
  remain intact; ordinary refreshes preserve unfinished edits.
- Density remains editable for explicit reviewed alternatives. Editing the
  inherited density clears its automatic note so an override needs its own basis.
- Short field guidance replaces 'Required — no default'. Detailed boundaries
  remain in hover help. Equipment/Kv review and final Accept duty are unchanged.
- Clear removes the saved preview basis and offers a fresh draft; offering it
  does not make the preview ready or accept duty. No schema or upstream change.

Validation here: isolated production controller/pipe-constant checks, real
presentation-method checks, H-S73-B1 regressions, compilation, whitespace and
installer guards. Full Qt/application dependencies are unavailable in the
supplied subset. New H-S73-B2 and existing H-S73-A/B local suites and real-GUI
review remain pending. H-S74-A remains accepted/pushed as 53f424d. H-S73-B,
B1 and this B2 work are uncommitted; final required duty remains unaccepted.

Next: apply the guarded B2 patch; run B2, B1 and H-S73-A/B tests; inspect Pump,
review the inherited basis and Apply explicitly, then review equipment/Kv in
Duty. No Git action, manufacturer selection or automatic engineering acceptance.
Preserve all projects, notes, unrelated edits, backups and GPLv3 core boundaries.

## H-S73-B1 prepared — Pump route identity repair — 4 October 2026

Verified runtime trace and saved project establish that Recommit succeeds:
a new typed snapshot remains on the same project and both Pump views refresh.
The first common-main section is present with 0.34928229665071775 kg/s.
Its membership uses leg_id:subleg_id, while committed chosen-route IDs use
subleg_id. H-S73-A's literal comparison therefore falsely blocks full coverage.

The focused repair bridges qualified frozen membership to the explicit
committed route-ID set. Exact IDs remain supported; unknown, duplicate,
ambiguous or incomplete membership is rejected. A unique order-1 common-main
section with positive finite flow is still required. No flow summation,
snapshot rewriting, live topology fallback or automatic duty acceptance.

Scope: pump_preview_controller_v1.py, one H-S73-B1 regression test, this
checkpoint and CODE_MAP.md. Isolated controller tests and matching against the
supplied saved snapshot pass. Full repository/GUI validation remains pending;
the supplied source subset lacks HVAC.core dependencies for a full local run.
H-S73-B local tests passed before this repair. H-S74-A remains accepted and
committed/pushed as 53f424d; H-S73-B remains local and final duty unaccepted.

Next: run H-S73-B1 plus existing H-S73-A/B tests; inspect Pump / Preliminary.
The false common-main blocker should disappear; the designer must still enter
and apply the explicit density/common-loss/head-margin basis. Then review Duty.
Preserve all projects, notes, backups and unrelated work. No Git action here.

## H-S73-B local verification and Pump refresh investigation — 4 October 2026

Verified from Ian's terminal output and supplied source:
- H-S74-A is committed/pushed as 53f424d on phase-hydronics-h-a.
  Wizard operation is accepted; Education wording refinement is deferred.
- On 3 October both local H-S73-B dev tests passed and git diff --check
  was clean. H-S73-B remains uncommitted; final pump duty is unaccepted.
- The real application printed a successful REVERSE_RETURN proportioning
  commit. This proves the commit handler reached its success message, but
  does not by itself prove the snapshot remained available downstream.
- Pump / Preliminary subsequently displayed 'Commit a proportioning hydraulic
  basis first.' Runtime acceptance of the Pump interface remains blocked.
- Source review confirms button wiring and a missing visible success
  acknowledgement. The supplied context and Basic refresh code do not show
  the snapshot being cleared. The live cause is not yet established.
- A temporary diagnostic launcher records project/snapshot identity, Pump
  controller results, rendered status and changes during an explicit commit.
  It changes no source code or engineering rules and performs no Git actions.

Next: capture one actual Recommit and both Pump views, identify the cause,
then implement and validate a focused repair. Preserve unrelated work,
projects, notes and backups. No automatic duty acceptance or readiness bypass.

## H-S74-A locally accepted — 2 October 2026

Ian confirms the Topology Arranger Wizard works correctly. All five steps
were visually reviewed; direct controls are visible with Wizard off.
The Kitchen (DEV) screenshot was taken with no job loaded, as Ian clarified.
Education text refinements are deferred. This acceptance supersedes earlier
pending local H-S74-A acceptance notes below.

Both H-S74-A tests and compilation of the eight scoped Python files pass
in a temporary copy of committed fff7ae0 with only H-S74-A added, checked by
the scoped commit helper before staging. The helper also checks staged
whitespace and the exact ten-file scope before committing.

H-S73-B-associated local work is preserved separately; complete local
validation remains unconfirmed. Final pump duty remains unaccepted.
Next: verify H-S73-B equipment losses and generic Kv/Kvs in the local
repository, then review the Duty interface and explicit acceptance boundary.

## Local verification checkpoint — 1 October 2026

- HEAD and origin/phase-hydronics-h-a reported at fff7ae0.
  H-S73-A pump preview is committed/pushed; final duty remains unaccepted.
- H-S74-A is applied and uncommitted. Ian reports both topology tests
  passed and git diff --check was clean.
- Real-workspace screenshot reviewed: Wizard Start and matching Standard
  Education are visible and readable. Some schematic labels are truncated;
  access to rooms beyond the visible canvas still needs checking.
- Remaining Wizard steps and Ian's overall runtime acceptance are pending.
- H-S73-B-associated source files, documentation and backups are present.
  Complete local application and local test results remain unverified.
- Nothing was staged in the supplied status. Shared documentation contains
  both stages and needs selective staging for an H-S74-A-only commit.
- Preserve unrelated changes, projects, notes and backups.

## H-S74-A implementation checkpoint — 29 September 2026

Topology Arranger guidance and contextual Education, prepared from the supplied
`fff7ae0` source. This GUI-only stage is independent of the H-S73-B pump patch;
its delivery does not assert that H-S73-B was applied or accepted locally.

- A persistent **Wizard** checkbox enables Start → Legs → Branches → Rooms →
  Review. It reveals the same existing controls, preserving current inputs
  when switching modes. Back/Next only changes presentation; there is no
  automatic topology creation, engineering acceptance or completion flag.
- Staging tray text remains readable against its existing pale background in
  both Light and Dark schemes.
- Eight topology Education topics have Beginner, Standard and Classical text.
  Field focus and wizard steps select the topic; **?** opens the existing
  Education panel without moving it or the Navigation panel. Education level
  controls and reading/scrolling retain the current explanatory topic.
- The guide explains existing leg/principal creation, recursive branches and
  origins, staging, placement, order and index/terminal actions. It explicitly
  describes the adapter's limited legacy order/index editing scope.
- Existing creation, placement, index and validation paths remain authoritative.
  Wizard controls do not generate topology or override blockers. The adapter's
  existing DEV seed behaviour is not extended. Existing generated room-list
  routes must still be reviewed against the intended installation.
- Wizard on/off is a GUI QSettings preference (`topology/wizard_enabled_v1`),
  default off. Step position is session-local and resets on project change;
  a project swap clears creation-label drafts and previous creation messages.
  No ProjectState schema, physics, pipe sizing or GPLv3 boundary changes.

Validation in the supplied source copy: compilation; H-S74-A content, real
panel/adapter and MainWindow tests; fresh-process on/off persistence; nearby
Topology creation/branch/placement, Education and Navigation integration
regressions; offscreen visual review and guarded installer checks.
Ian accepted local Wizard operation on 2 October 2026; Education wording is deferred.

Run locally:
`QT_QPA_PLATFORM=offscreen PYTHONPATH=. python HVAC/dev/test_hs74a_topology_guidance_v1.py`
`QT_QPA_PLATFORM=offscreen PYTHONPATH=. python HVAC/dev/test_hs74a_topology_help_integration_v1.py`

Local Wizard acceptance is recorded above. Extension of the help pattern to
return arrangement and pipe inputs remains deferred.

## H-S73-B implementation checkpoint — 27 September 2026

Based on committed H-S73-A `fff7ae0`. This checkpoint supersedes the H-S73-A
next-stage deferrals below. Local runtime acceptance by Ian is still pending.

- Pump now has **Preliminary** and **Duty** views. Preliminary retains H-S73-A.
- Duty takes explicit additional equipment loss and a source note for every
  committed route (including explicit zero), plus operating Kv for each frozen
  positive-duty valve point. It reuses committed Kvs, point flow and membership.
- Liquid valve loss: `dp_Pa = 100000 * (rho/1000) * (Q_m3_h/Kv)^2`.
  Kvs gives rated-loss evidence; blank operating Kv permits preview only.
  Operating Kv must be positive and no greater than the committed Kvs.
  Non-cavitating liquid basis must be reviewed; viscosity corrections and
  upstream fluid/friction recalculation are outside this stage.
- Route total is committed chosen pipework (including shared pipes and Local K)
  plus additional equipment plus actual generic valve loss. Old balancing
  allocations are comparison evidence only, never added again. Shared valve
  loss uses total point flow and enters each governed route once.
- The controlling route is recalculated after these additions. Flow still comes
  from the committed first common main. Explicit common loss and head reserve
  are applied after the maximum route total, once.
- Explicit **Accept duty** requires complete inputs, reviewed equipment/control
  assumptions, explicit operating Kv and route residuals no greater than 0.05 Pa.
  Residuals are against the highest route total, before the common allowance and
  head reserve. No automatic Kv selection or balancing setting is introduced.
- ProjectState optionally persists `hydronic_pump_duty_basis` and a separate
  `hydronic_pump_duty_acceptance`. Only the controller writes them. Acceptance
  resolves only against its exact current reviewed basis and recomputed duty;
  changed snapshot, density, common loss, margin or detailed inputs invalidate it.
  Consumers must use `preview_pump_duty_v1(...).accepted`, not field presence.
- This accepts a **required parameter-based design duty**, not a selected pump,
  whole-system completion or manufacturer curve verification. No product,
  efficiency, NPSH or installation suitability is inferred. Manufacturers remain
  optional. Navigation, upstream sizing and GPLv3 boundaries are unchanged.

Validation in the supplied source copy on 27 September 2026: changed Python
files compile; H-S73-B arithmetic/persistence and real panel/adapter tests pass;
H-S73-A, H-S56-C, H-S70-B1 and H-S72-A4F integration regressions pass.
Offscreen dark-theme Pump tabs visually inspected. Minimal-fixture topology
messages and Qt offscreen platform messages do not fail the assertions.
The guarded installer and whitespace checks are verified before delivery.

Run locally:
`QT_QPA_PLATFORM=offscreen PYTHONPATH=. python HVAC/dev/test_hs73b_pump_duty_v1.py`
`QT_QPA_PLATFORM=offscreen PYTHONPATH=. python HVAC/dev/test_hs73b_pump_duty_gui_v1.py`
Then inspect Hydronics → Pump → Duty with a real committed project. Final
acceptance is the designer's explicit action; no stored project is auto-accepted.
Next: Ian's runtime acceptance and scoped checkpoint; optional pump-curve
assessment is a separate stage, not a condition of parameter-based completion.

## H-S72-A4F accepted — 26 September 2026

Navigation GUI checkpoint, based on `6643ca0`.

- Each saved view has a persistent **In Navigation** checkbox; selected views
  appear as compact buttons, including custom and renamed views.
- Buttons wrap to the available width. Overflow scrolls without enlarging the
  floating Navigation window; the existing orange/dark-text focus is retained.
- Membership changes update immediately without switching Main/Exploded mode.
  Return Schematic remains available with the Proportioning view.
- Navigation retains independent floating position, size, visibility and restart
  restoration. Closing/reopening and deliberate docking remain supported.
- GUI preferences only: no engineering, ProjectState or GPLv3 boundary changes.

Accepted from Ian's runtime screenshot and terminal results on 26 September:
compilation; H-S72-A4F membership and real MainWindow integration;
H-S72-A4D floating isolation; H-S72-A4E fresh-process restart; clean diff check.
Navigation is accepted for this stage. Engineering work continues separately.

## H-S73-A validated preview — 26 September 2026

Implementation based on `6643ca0` (Navigation floating/restart persistence).
This checkpoint supersedes the historical next-stage notes below; the
engineering boundaries remain in force. H-S73-A adds a **Pump** tab inside
Hydronics, reachable from Results, for a preliminary committed-snapshot duty.

- Controller owns readiness and writes explicit user preview intent only.
- System mass flow comes from the first committed common-main section covering
  all committed routes. Missing/ambiguous coverage blocks the preview.
- Pressure uses the maximum chosen route total, already including shared mains
  and Local K once. Route flows/pressures are never summed to obtain pump duty.
- Density, additional loss common to every route, head margin and their source
  note must be explicitly entered and applied. Zero allowances are allowed;
  no default water density, safety factor, flow margin or efficiency is inserted.
- Optional `ProjectState.hydronic_pump_preview_basis` persists intent only.
  A changed committed snapshot invalidates that basis until reviewed/reapplied.
  Unsaved live edits do not change this explicitly labelled committed-basis review.
- A ready preview is not accepted final duty. Route-specific equipment losses,
  complete balancing/control requirements (including generic Kv/Kvs and their
  pressure-loss consequences) and final parameter acceptance remain
  for the next stage. **A finished design can be parameter-based: manufacturer
  or model selection is optional, never a completion prerequisite.**
- No changes to Navigation ownership, pump product selection, upstream sizing,
  physics/friction solvers, or GPLv3 core/add-on boundaries.

Validation passed locally on 26 September 2026:
- Pump modules and `ProjectState` compiled successfully.
- `QT_QPA_PLATFORM=offscreen PYTHONPATH=. python HVAC/dev/test_hs73a_pump_duty_preview_v1.py`
  passed numerical duty, explicit assumptions, no double counting, stale-snapshot
  rejection, persistence and real-widget integration checks.
- `git diff --check` was clean.
- Two wider-panel topology diagnostics arose from the minimal test projects;
  the pump-preview assertions passed.

H-S73-A is validated as a preliminary committed-basis preview. Final pump-duty
acceptance and route-specific equipment/Kv/Kvs consequences remain deferred.
Next: complete per-route component-loss, generic Kv/Kvs and control basis, then explicit
acceptance/display of the parameter-based pump duty. Do not require a catalogue.

## Historical baseline (5 July 2026)

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
