# HVACgooee — COMMIT POLICY (LOCKED)

Timestamp (UK):
Monday 26 January 2026, 03:42 am

Status:
🔒 LOCKED — AUTHORITATIVE

---

## Purpose

This document defines what a **commit / save** means in HVACgooee.

It exists to prevent ambiguity, optimisation creep, and accidental
re-introduction of legacy behaviours.

Once locked, this policy must not be weakened without a formal
architecture revision.

---

## Canonical Definitions

### Project
A Project is a **complete, serialisable snapshot** of engineering intent,
results, and explicit validity flags.

### Runtime Buffer
The runtime buffer is **all in-memory, transient state**:
- active ProjectModel instance
- cached DTOs
- runner state
- GUI selections

The runtime buffer is **never authoritative**.

---

## Save / Commit Rules (LOCKED)

### 1. Save is Snapshot-Based

- Every save writes a **full project snapshot**
- No partial updates
- No deltas
- No journaling
- No replay logic

> Save = write the whole truth

---

### 2. Update vs Save

- Updates occur **in memory only**
- Disk persistence is **snapshot-only**

> Updates are for buffers, not for disk

---

### 3. Backups

- Every save creates a timestamped backup
- Backups are stored in:
  `.project_backups/`
- Backup files are small (KB-scale)
- Backups are automatic and silent

Backups exist for **safety**, not history.

---

### 4. Archive / Baseline

- Archive is an **explicit user action**
- Archive keeps **1–3 known-good snapshots**
- Archive files live in:
  `.project_archive/`
- Archive is recoverable and intentional
- Archive never auto-triggers

Archive exists for **meaning**, not safety.

---

### 5. Pruning

- Pruning is **explicit only**
- Never triggered automatically by save
- User selects pruning level:
  - Light (keep 50)
  - Normal (keep 25)
  - Aggressive (keep 10)
  - Archive / Baseline (keep 1)

---

### 6. Load Behaviour (CRITICAL)

- Loading a project **always clears the runtime buffer**
- In-memory state is discarded
- ProjectModel is replaced entirely
- No auto-runs occur
- Validity flags are trusted

> Load = Ctrl-Break → clear buffer → restart

---

## Prohibited Patterns

The following are explicitly forbidden:

- Partial project saves
- Delta / patch files
- Auto-pruning on save
- Auto-running engines on load
- Reusing runtime state across project loads
- Treating backups as authoritative

---

## One-Line Authority Rule

> Projects are snapshots.  
> Buffers are temporary.  
> Commits write truth.

🔒 END OF COMMIT POLICY

## Project Persistence & Authority (v3) — LOCKED

### Architectural Level

This section defines project authority, persistence, and lifecycle rules
at the platform level.

---

### Authority Boundaries

| Layer | Owns |
|-----|-----|
| ProjectModelV3 | Truth, intent, results, validity |
| Runtime Buffer | Temporary state only |
| IO v3 | Translation to/from disk |
| Runners | Execution order |
| Engines | Calculations only |
| GUI | Observation + intent editing |

No layer may exceed its authority.

---

### Persistence Model

- Projects are persisted as **full snapshots**
- Storage format is implementation detail (currently JSON)
- One authoritative file per project:
  `project.json`

Persistence is **stateless and deterministic**.

---

### Runtime Reset Rule (CRITICAL)

On project load:

1. Runtime buffer is cleared
2. In-memory project is discarded
3. ProjectModel is replaced
4. GUI rebinds as observer
5. No calculations auto-run

This behaviour is mandatory.

---

### Safety Model

- Automatic backups provide recovery
- Archive / Baseline provides meaning
- Pruning is user-controlled
- Deletion is explicit

---

### Legacy Compatibility

Legacy project formats may be:
- imported
- migrated
- adapted

They must not define authority.

---

### Architectural One-Liners (LOCKED)

- Projects decide; engines calculate
- Validity is explicit, never inferred
- Runtime state is disposable
- Disk state is authoritative
- Clearing the buffer restores truth

🔒 END OF SECTION
