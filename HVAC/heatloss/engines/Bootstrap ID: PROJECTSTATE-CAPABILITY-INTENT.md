======================================================================
HVACgooee — ProjectState Capability Intent
Bootstrap ID: PROJECTSTATE-CAPABILITY-INTENT
Date: Monday 6 February 2026, 18:34 pm
Status: ACTIVE — intent lock
======================================================================
Purpose

This bootstrap defines how capability intent is expressed in ProjectState.

It exists to:

Allow projects to declare what level of capability they intend to use

Decouple capability intent from:

GUI modes

engine implementation

add-on installation

Provide a stable switchpoint for controllers

Avoid future ProjectState rewrites

This document defines representation only — not execution.

Core Principle (LOCKED)

ProjectState declares intent, not availability.

ProjectState may request a capability that is not installed

ProjectState never checks licensing

ProjectState never selects engines

ProjectState never imports add-ons

It simply states:

“This project intends to be solved at this capability level.”

What “Capability” Means

A capability is the depth and responsibility of a calculation.

Examples:

simple vs advanced heat-loss physics

steady-state vs dynamic simulation

indicative vs compliance-grade outputs

Capability is:

project-scoped

explicit

serialisable

user-controlled

Canonical Location in ProjectState (LOCKED)

Capability intent lives in ProjectState, not GUI config.

Conceptual structure
ProjectState.capabilities


This object:

is part of the saved project

is editable by explicit user action

is read-only to GUI observers

is consulted by controllers only

Canonical Shape (Intent-Only)
Minimal, future-proof structure
@dataclass
class CapabilityIntent:
    heatloss: str = "simple"
    hydronics: str = "simple"
    # future domains may be added:
    # acoustics: str
    # lighting: str


Stored as:

ProjectState.capabilities: CapabilityIntent

Allowed Values (v1)

For heat-loss:

"novice"

"simple" ← default for v1

"professional"

Notes:

"professional" expresses intent

It does NOT imply availability

It does NOT imply Advanced engine is installed

Defaults (LOCKED)

When a new project is created:

ProjectState.capabilities.heatloss = "simple"


This ensures:

v1 stability

predictable behaviour

no surprise physics

Behavioural Guarantees (LOCKED)

Changing capability intent:

❌ does not run calculations

❌ does not mutate results

❌ does not validate availability

❌ does not change GUI mode

❌ does not load add-ons

It simply updates project intent.

Who Reads Capability Intent
Controllers (Allowed)

Controllers may:

inspect ProjectState.capabilities

select appropriate execution paths

decide whether execution is possible

Controllers must handle:

unavailable capabilities gracefully

fallback or disable execution explicitly

GUI (Observer Only)

GUI:

may display current capability intent

may allow explicit user change

must not infer behaviour

must not check licensing

must not decide availability

Who Must NOT Use Capability Intent

Explicitly forbidden:

engines

DTOs

geometry models

construction models

readiness adapters

result storage

Capability intent is not physics.

Serialization (LOCKED)

Capability intent:

must be serialised with the project

must survive load/save round-trips

must not affect backward compatibility

Projects created before this field existed:

default to "simple"

Non-Goals (Explicit)

This bootstrap does NOT:

define engine routing

define add-on discovery

define licensing enforcement

define GUI mode behaviour

define fallback strategies

Each of these requires its own bootstrap.

Architectural Ethos (Re-affirmed)

ProjectState represents what the project wants to be,
not what the installation can do.

That distinction protects:

openness

clarity

future extensibility

user trust

Freeze Statement (Pending)

This bootstrap will be frozen once:

CapabilityIntent is added to ProjectState

defaults are wired into project creation

serialization is confirmed

All future capability logic must reference this document.
