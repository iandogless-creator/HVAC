======================================================================
HVACgooee Bootstrap — Phase K-C: Persistence Writer & Atomic Commit

Bootstrap ID: BL-KC-PERSIST
Phase: K-C (Persistence & Commit Mechanics)
Status: ACTIVE (authoritative)
Date: 2026-02-12

1. Purpose

Phase K-C formalises how projects are written to disk, not when or why.

This phase exists to:

Implement atomic, crash-safe persistence

Enforce the already-locked COMMIT POLICY

Guarantee backups are created correctly and silently

Prevent partial, corrupted, or ambiguous project writes

Phase K-C does not redefine commit semantics.
All meaning of “save”, “backup”, “archive”, and “authority” is inherited verbatim from COMMIT.md.

2. Canonical Reference (LOCKED)

This phase explicitly depends on:

HVACgooee — COMMIT POLICY (LOCKED)
COMMIT.md

That document is the single authority on:

What a commit means

Snapshot semantics

Backup and archive intent

Runtime buffer invalidation

Phase K-C only defines how IO obeys that policy.

No rule in this bootstrap may weaken, reinterpret, or bypass COMMIT.md.

3. Authority Boundaries (LOCKED)
3.1 IO / Persistence Layer Responsibilities

The persistence layer is responsible for:

Writing a complete project snapshot

Performing an atomic commit

Creating automatic backups

Never mutating in-memory ProjectState

Never triggering calculations

Never inferring intent

The persistence layer has no authority over:

Save eligibility

Legacy upgrade decisions

Project completeness

Run readiness

3.2 ProjectState Responsibilities (unchanged)

ProjectState remains the sole authority for:

In-memory truth

Identity

Results

Save eligibility flags

ProjectState does not write files directly.

4. Atomic Write Contract (LOCKED)

All project saves MUST be atomic.

4.1 Required Atomic Sequence

When saving project.json, IO MUST perform the following steps in order:

Serialize the entire ProjectState to a temporary file

Example: project.json.tmp

Flush and sync the temporary file

Ensure bytes are physically written

Rename temporary file → project.json

Atomic replace (POSIX-safe rename)

Only after successful rename:

Update in-memory “last saved” markers (if any)

If any step fails:

The original project.json remains untouched

The save is considered failed

No partial file may remain authoritative

4.2 Forbidden Patterns (LOCKED)

The following are explicitly forbidden:

Writing directly to project.json

In-place mutation of an existing file

Partial writes

Streaming / incremental updates

JSON patching

Journaling

Multi-file commit logic

Save = write the whole truth (as defined in COMMIT.md)

5. Backup Enforcement (Inherited, Explicit)
5.1 Backup Creation Rule

As defined in COMMIT.md:

Every successful save MUST create a backup

Backup creation is automatic and silent

Backups are not authoritative

Phase K-C enforces this mechanically.

5.2 Backup Ordering (LOCKED)

Backup creation MUST occur:

Before the new project.json replaces the old one

Using the previous authoritative snapshot

Typical sequence:

Existing project.json → copy to .project_backups/

Perform atomic write of new snapshot

Commit completes

Backups MUST NOT be created if the save fails.

5.3 Backup Naming & Location (Inherited)

Backup location and naming are inherited directly from COMMIT.md:

Directory: .project_backups/

Timestamped filenames

Small, snapshot-complete files

Phase K-C does not redefine pruning or retention.

6. Archive / Baseline (Out of Scope, Referenced)

Archive / baseline behaviour is explicitly out of scope for Phase K-C.

Phase K-C must:

Provide the same atomic guarantees for archive writes

Defer all archive intent, retention, and UX to higher layers

All archive semantics remain governed by COMMIT.md.

7. Load Safety Interaction (LOCKED)

Atomic write guarantees are required because:

Load always clears runtime buffers

Load trusts disk state as authoritative

Corrupt or partial files are unacceptable

Phase K-C guarantees that:

Any successfully written project.json is load-safe.

8. Failure Semantics (Intentional)

The following behaviours are correct and final:

Situation	Behaviour
Disk full / permission error	Save fails, original file untouched
Crash during temp write	No effect on authoritative file
Crash before rename	Old project remains authoritative
Crash after rename	New project authoritative
Backup creation fails	Save fails (do not proceed)

No silent recovery is allowed.

9. What Becomes Stable After Phase K-C

LOCKED after this bootstrap:

Atomic save sequence

Backup enforcement ordering

Separation of commit semantics vs IO mechanics

Prohibition of partial writes

Crash-safe persistence guarantees

Any future changes must be additive, not corrective.

10. Next Canonical Step (Not Part of This Bootstrap)

Phase K-D

Dirty-state tracking (what changed)

Save prompts (“unsaved changes”)

Manual restore from backup UX

Diff / compare tooling (optional)

End of Bootstrap

Absolutely — this is the right moment to lock it while the model is clean.

Below is Phase K-D, written to sit cleanly on top of COMMIT.md, K-B, and K-C, without redefining any lower-level rules.

======================================================================
HVACgooee Bootstrap — Phase K-D: Dirty State, Save Prompts & Backup Restore

Bootstrap ID: BL-KD-DIRTY-RESTORE
Phase: K-D (Persistence UX & Safety)
Status: ACTIVE (authoritative)
Date: 2026-02-12

1. Purpose

Phase K-D formalises user-visible persistence safety, without changing
commit semantics or IO mechanics.

This phase defines:

Dirty-state tracking (unsaved changes)

Save prompting rules (when and how the user is warned)

Backup restore workflow (explicit, safe, non-authoritative)

Exit / load protection against accidental data loss

Phase K-D is UX-facing but authority-respecting:
it observes authoritative state and commit outcomes, but never invents truth.

2. Canonical Dependencies (LOCKED)

This phase explicitly depends on:

COMMIT.md — snapshot & backup semantics

Phase K-B — save eligibility & legacy handling

Phase K-C — atomic write & backup enforcement

No rule in Phase K-D may override or weaken those documents.

3. Canonical Definitions (LOCKED)
3.1 Dirty State

A project is dirty if:

In-memory ProjectState differs from the last committed snapshot

Dirty state is:

Binary (dirty / clean)

Project-scoped

Non-authoritative (derived, not persisted)

Dirty state does not imply:

Invalidity

Incompleteness

Need to run engines

3.2 Clean State

A project is clean if:

It exactly matches the last successfully committed snapshot

On load:

All projects start clean

3.3 Last Committed Snapshot

The “last committed snapshot” is:

The ProjectState that was successfully written via Phase K-C

The authoritative baseline for dirty comparison

Backups and archives are not baselines.

4. Authority Boundaries (LOCKED)
4.1 ProjectState Responsibilities

ProjectState MUST:

Expose a read-only is_dirty flag

Expose a read-only dirty_reason (optional, human-readable)

Reset dirty state only after a successful commit

ProjectState MUST NOT:

Prompt the user

Save files

Restore backups

Track UI-only state

4.2 GUI Responsibilities

GUI MAY:

Display dirty indicators (e.g. “*” in title)

Prompt user before destructive actions

Offer save / discard / cancel choices

Offer explicit backup restore actions

GUI MUST NOT:

Infer commit success

Clear dirty state manually

Modify ProjectState during prompts

4.3 IO Responsibilities

IO MUST:

Notify caller of successful commit

Notify caller of failed commit

Never mutate dirty state directly

5. Dirty-State Tracking Rules (LOCKED)
5.1 What Marks a Project Dirty

A project becomes dirty when:

Any authoritative ProjectState field changes

Any committed result is invalidated

Any identity-valid edit occurs (name, reference, etc.)

Dirty tracking must be coarse-grained:

No per-field diffing required

No partial dirty states

5.2 What Does NOT Affect Dirty State

The following MUST NOT mark a project dirty:

GUI selection (active room, panel focus)

Hover / preview overlays

Education panel changes

Runtime buffers

Transient DTOs

Adapter refreshes

6. Save Prompt Rules (LOCKED)
6.1 Prompt Triggers

GUI MUST prompt the user if the project is dirty and the user attempts to:

Load another project

Close the project

Exit the application

Restore from backup

Upgrade legacy project (if current project is dirty)

6.2 Prompt Options

The prompt MUST offer exactly:

Save (if save-eligible)

Discard changes

Cancel

If the project is not save-eligible, the Save option must be disabled with a reason from Phase K-B.

6.3 Save Outcome Handling

If Save succeeds → project becomes clean

If Save fails → project remains dirty

If Discard → reload last committed snapshot

If Cancel → no action

No silent fallback is allowed.

7. Backup Restore Workflow (LOCKED)
7.1 Restore Intent

Backup restore is:

Explicit

User-initiated

Destructive to in-memory state

Backups are never authoritative until explicitly restored and committed.

7.2 Restore Sequence

User selects a backup snapshot

If current project is dirty → save prompt shown

Backup snapshot is loaded into ProjectState

ProjectState is marked dirty

Save eligibility is re-evaluated

User must explicitly save to commit restored state

7.3 Forbidden Restore Behaviour

The following are forbidden:

Auto-restoring on startup

Silent restore

Treating backups as authoritative

Overwriting project.json without explicit save

8. Failure Semantics (Intentional)
Situation	Behaviour
User exits with dirty project	Prompt shown
Save fails during prompt	Remain dirty
Backup restore fails	No state change
Restore over legacy project	Must go through upgrade rules
Discard selected	Reload last committed snapshot
9. What Becomes Stable After Phase K-D

LOCKED after this phase:

Dirty state definition

Save prompt rules

Backup restore semantics

GUI / ProjectState authority split

Non-authoritative nature of dirty tracking

Any future enhancements must be additive only.

10. Next Canonical Step (Not Part of This Bootstrap)

Phase K-E

Multi-project sessions

Diff / compare UI

Timed autosave (non-authoritative scratch)

“Save As” flows

Collaboration groundwork (future)
