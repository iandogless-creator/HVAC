/home/vagggn/PycharmProjects/PythonProject/HVAC/.venv/bin/python /home/vagggn/Work/PycharmProjects/PythonProject/HVAC/examples/vertical_stack_demo.py
⚠️ flowrate module not found — using placeholder data.

==============================
HVACgooee — Horizontal Vertical Stack Demo
EURIKA v1 — Authoritative Pipeline
==============================

--- ROOM: room-001 ---
Ti = 21.0 °C
Te = -3.0 °C
floor        | A=12.00 | U=0.22 | dT=24.00 | Qf=63.36 | EXTERNAL → EXT
ceiling      | A=12.00 | U=0.25 | dT=1.00 | Qf=3.00 | INTER_ROOM → room-002
wall         | A=12.00 | U=0.28 | dT=3.00 | Qf=10.08 | INTER_ROOM → room-004
ΣQf = 76.44 W

--- ROOM: room-002 ---
Ti = 20.0 °C
Te = -3.0 °C
floor        | A=12.00 | U=0.25 | dT=-1.00 | Qf=-3.00 | INTER_ROOM → room-001
ceiling      | A=12.00 | U=0.25 | dT=-3.00 | Qf=-9.00 | INTER_ROOM → room-003
wall         | A=12.00 | U=0.28 | dT=-2.00 | Qf=-6.72 | INTER_ROOM → room-005
ΣQf = -18.72 W

--- ROOM: room-003 ---
Ti = 23.0 °C
Te = -3.0 °C
floor        | A=12.00 | U=0.25 | dT=3.00 | Qf=9.00 | INTER_ROOM → room-002
ceiling      | A=12.00 | U=0.18 | dT=26.00 | Qf=56.16 | EXTERNAL → EXT
wall         | A=12.00 | U=0.28 | dT=-2.00 | Qf=-6.72 | INTER_ROOM → room-006
ΣQf = 58.44 W

--- ROOM: room-004 ---
Ti = 18.0 °C
Te = -3.0 °C
wall         | A=12.00 | U=0.28 | dT=-3.00 | Qf=-10.08 | INTER_ROOM → room-001
ΣQf = -10.08 W

--- ROOM: room-005 ---
Ti = 22.0 °C
Te = -3.0 °C
wall         | A=12.00 | U=0.28 | dT=2.00 | Qf=6.72 | INTER_ROOM → room-002
ΣQf = 6.72 W

--- ROOM: room-006 ---
Ti = 25.0 °C
Te = -3.0 °C
wall         | A=12.00 | U=0.28 | dT=2.00 | Qf=6.72 | INTER_ROOM → room-003
ΣQf = 6.72 W

Process finished with exit code 0
