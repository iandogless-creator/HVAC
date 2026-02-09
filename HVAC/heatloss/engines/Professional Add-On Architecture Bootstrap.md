======================================================================
HVACgooee — Professional Add-On Architecture Bootstrap
Bootstrap ID: ADDON-PROFESSIONAL-CAPABILITIES
Date: Monday 6 February 2026, 18:12 pm
Status: ACTIVE — intent lock
======================================================================
Purpose

This bootstrap defines the architectural intent for professional add-on
packages in HVACgooee.

It exists to:

Enable advanced, liability-grade capabilities

Preserve a fully open and usable core

Support ethical dual licensing

Avoid GUI or workflow fragmentation

Prevent future authority bleed into the core

This document defines what add-ons are, what they are not, and where
they integrate.

Core Principle (LOCKED)

Add-ons provide capability, not permission.

All GUI modes may access all installed add-ons

Modes never gate add-ons

Add-ons never change workflow semantics

Add-ons never replace or cripple the core

Relationship to Core
HVACgooee Core (Always Present)

GPLv3

Fully functional for real engineering work

Includes:

ProjectState

GUI v3

Heat-Loss Simple engine (v1)

Hydronics v1

Worksheet-based workflow

Explicit execution model

The core must remain:

honest

complete

usable

defensible for learning and practice

Professional Add-On Package (Primary)
Package Concept

hvacgooee-professional

A capability add-on intended for professional engineers who require:

deeper physics

compliance-grade confidence

defensible outputs

reduced professional risk

This package is optional and never required to use HVACgooee.

Capabilities Provided (Indicative, Not Exhaustive)
Heat-Loss (Advanced)

ψ-value handling

Y-value handling

dynamic thermal mass

decrement factors

climate / exposure modifiers

extended result breakdowns

audit-friendly reporting hooks

Reporting & Compliance

traceable calculation breakdowns

assumption listings

reproducible outputs

future regulatory adapters

Extended Physics (Future)

dynamic response

time-dependent loads

advanced boundary conditions

Other Potential Add-Ons (Explicitly Allowed)

This bootstrap does not limit add-ons to heat-loss.

Future add-ons may include:

acoustics

lighting

dynamic simulation

compliance exporters

BIM / CAD bridges

enterprise data connectors

Each add-on:

is independently installable

declares its own capabilities

integrates via controllers, not GUI panels

Integration Rules (LOCKED)
1️⃣ ProjectState Is the Switchpoint

ProjectState declares capability intent

ProjectState does not import add-ons

Add-ons never mutate ProjectState structure

Example (conceptual):

project_state.capabilities.heatloss = "advanced"


No engine selection occurs in the GUI.

2️⃣ Controllers Select Engines

Controllers detect available add-ons

Controllers select execution engines

Controllers remain deterministic

GUI remains observer-only

3️⃣ GUI Remains Neutral

GUI v3:

does not know which add-ons are paid

does not advertise licensing

does not upsell

does not block workflows

If a capability is unavailable:

execution is gracefully disabled

neutral messaging only

Licensing Intent (LOCKED)

Core remains GPLv3

Professional add-ons may be:

commercial

dual-licensed

Add-ons never re-license the core

No runtime licence checks in core modules

Licensing enforcement, if any, lives outside the core.

Non-Goals (Explicit)

This bootstrap does NOT:

implement add-on loading

define pricing

add licence enforcement

modify GUI workflows

alter ProjectState schema

Those require separate bootstraps.

Architectural Ethos (Re-affirmed)

HVACgooee prioritises:

engineering honesty

calm workflows

explicit intent

long-term trust

ethical sustainability

Professional users pay for depth and responsibility,
not for access to basic functionality.

Freeze Statement (Pending)

This bootstrap will be frozen once:

ProjectState capability intent is formalised

Controller execution routing is defined

Simple engine v1 is locked

All future add-on work must reference this document.

NOTE:
Engine capability selection is intentionally deferred beyond v1.
Architecture allows for multiple entry engines in future versions.

