# HVACgooee — GUI v3 Phase G-C Freeze

Status: FROZEN
Date: 2026-02-17
Phase ID: GUI-V3-PHASE-G-C

---

## Purpose

This file is an **index / pointer only** for Phase G-C.

It records that Phase G-C is frozen and identifies the **single
authoritative freeze document** that defines the rules for this phase.

No architectural rules are defined here.

---

## Authoritative Freeze (LOCKED)

**Heat-Loss Worksheet & HLPE Spine**

→ `panels/Heat-Loss Worksheet & HLPE Spine.md`

This document is the sole authority for:

• Heat-Loss worksheet behaviour
• HLPE (Heat-Loss Edit Overlay) interaction model
• Non-positional edit signal routing
• Observer-only GUI boundaries

---

## Scope Summary (Non-Normative)

Phase G-C establishes that:

• The Heat-Loss worksheet renders deterministically
• Worksheet rows are observer-populated
• Editing is performed exclusively via HLPE
• No calculations are required to validate interaction flow

All calculation, validation, and authority remain outside the GUI.

---

## Change Policy

Any change that affects the worksheet–HLPE interaction model,
signal routing, or authority boundaries **must advance to Phase H**.

Direct modification of the authoritative freeze document is forbidden.

---

© 1989–2026 HVACgooee Project
GPLv3 Core
