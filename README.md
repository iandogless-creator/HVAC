# HVACgooee

**HVACgooee** is an open, engineering-grade HVAC calculation framework written in Python.

It is designed to preserve and modernise traditional CIBSE-era methods — including U-values, steady-state heat-loss, hydronic sizing, and transparent engineering workflows — while providing a clean modular foundation for future extensions.

---

## Current Development Branch

Active development currently happens on:

`phase-iv-b-adjacency`

This branch contains the current GUI v3, heat-loss, topology, construction-authority, and adjacency work.

---

## Current Project State

For the current active development state, switch to the active branch and see:

- `CURRENT_STATE.md`
- `CODE_MAP.md`

The `main` branch is retained as the public/stable landing branch and may lag behind the active development branch.

---

## Project Direction

HVACgooee is being developed as a deterministic, topology-driven HVAC calculation engine.

The core principle is:

> engineering authority, physical computation, and GUI presentation must remain separate.

In practical terms:

- `ProjectState` owns engineering state
- engines compute physics
- constructions own U-values
- topology owns adjacency
- GUI panels observe and emit intent only

---

## Licence

HVACgooee core is released under GPLv3.

---

## Author

Ian Allison
