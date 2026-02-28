# 🔒 Thermal Hierarchy (Frozen)

This document defines the authoritative thermodynamic layering of HVACgooee.
It formalises where each quantity exists and who owns it.

This structure is frozen for Fabric + Ventilation phases.

---

# 1️⃣ Surface Level (Element Physics)

## Definition

\[
Q_{f,i} = U_i \cdot A_i \cdot \Delta T
\]

Where:

- \( U_i \) = surface U-value (W/m²K)
- \( A_i \) = surface area (m²)
- \( \Delta T \) = \( T_i - T_e \) (K)

## Rules

- Exists only inside the **Fabric Engine**
- Not stored independently in `ProjectState`
- Not persisted
- Used only to derive room-level aggregation

Surface physics is transient and engine-scoped.

---

# 2️⃣ Room Level (Authoritative Room Results)

Room is the first authoritative storage boundary.

## Fabric (Room Aggregation)

\[
\Sigma Q_f^{room} = \sum_i Q_{f,i}
\]

This represents the total fabric heat loss for a single room.

---

## Ventilation

\[
Q_v^{room} = 0.33 \cdot ACH \cdot Volume \cdot \Delta T
\]

Where:

- ACH = air changes per hour (1/h)
- Volume = room volume (m³)
- 0.33 = air constant (W per m³/h·K)

Ventilation is a room-level quantity.
It is **not** prefixed with Σ.

---

## Later (Room Total)

\[
Q_t^{room} = \Sigma Q_f^{room} + Q_v^{room}
\]

This will be introduced only after both subsystems are frozen.

---

## Room Owns


sum_qf_room_W
qv_room_W
qt_room_W # later


Naming Rules:

- Σ applies only to summed surfaces (fabric).
- Qv is already a room total and does not use Σ.
- Qt is the total room heat loss.

---

# 3️⃣ Project Level (Aggregation Only)

Project level performs no new physics.
It aggregates room-level results.

---

## Fabric (Project Aggregation)

\[
\Sigma Q_f^{project} = \sum \Sigma Q_f^{room}
\]

---

## Ventilation (Project Aggregation)

\[
\Sigma Q_v^{project} = \sum Q_v^{room}
\]

---

## Project Total

\[
Q_t^{project} = \Sigma Q_f^{project} + \Sigma Q_v^{project}
\]

---

## Project Owns Only Aggregates

Project does not compute surface physics.
Project does not compute room physics.
Project aggregates room-level authoritative results.

---

# Architectural Summary


Surface Level:
Qf_i

Room Level:
ΣQf_room
Qv_room
Qt_room (later)

Project Level:
ΣQf_project
ΣQv_project
Qt_project


---

# Freeze Guarantees

- Surface physics remains engine-scoped.
- Room is the first authoritative storage boundary.
- Project performs aggregation only.
- Ventilation does not depend on fabric internals.
- Fabric does not depend on ventilation.
- Qt is introduced only after both subsystems are stable.

This hierarchy is frozen for Fabric Phase II and Ventilation Phase V-A.
