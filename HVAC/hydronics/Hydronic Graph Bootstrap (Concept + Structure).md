HVACgooee — Hydronic Graph Bootstrap (Concept + Structure)

Timestamp: Saturday 15 March 2026 (UK)
Subsystem: Hydronic Topology Graph
Status: Architectural Bootstrap
Goal: Define the minimal structure required to represent a hydronic system as a graph.

1. Purpose of the Hydronic Graph

The hydronic graph represents the physical connectivity of the heating system.

It answers questions such as:

Which components are connected?
Where does flow travel?
What pipe lengths and diameters exist?
Where are emitters located?

The graph does not yet perform calculations.

It only defines topology.

2. Hydronic Graph Structure

The hydronic network is represented as a directed graph.

Nodes → Components
Edges → Pipes

Example:

Boiler → Pump → Radiator A → Radiator B → Return

Graphically:

[Boiler]
    │
    ▼
[Pump]
    │
    ▼
[Pipe]
    │
    ▼
[Radiator A]
    │
    ▼
[Pipe]
    │
    ▼
[Radiator B]
    │
    ▼
[Return]
3. Core Graph Elements

The minimal model requires only two entities.

HydronicNode

Represents a component.

Examples:

boiler
pump
radiator
manifold
valve
junction

Minimal structure:

node_id
node_type
room_id (optional)

Example:

node_001
type = radiator
room_id = room_A
HydronicEdge

Represents a pipe segment.

Minimal structure:

edge_id
start_node_id
end_node_id
length_m
diameter_mm

Example:

edge_004
start = pump
end = radiator_A
length = 4.2 m
diameter = 15 mm
4. HydronicGraph Container

The graph container holds nodes and edges.

Minimal structure:

HydronicGraph
    nodes: Dict[node_id → HydronicNode]
    edges: Dict[edge_id → HydronicEdge]

Example:

nodes:
    boiler
    pump
    radiator_A
    radiator_B

edges:
    pipe_1
    pipe_2
    pipe_3
5. Relationship to Thermal Model

The hydronic graph connects to the thermal graph through emitters.

Example:

Room A
   ↓ heat demand
Radiator A
   ↓
Pipe network
   ↓
Boiler

So the interface between the graphs becomes:

room_heat_load_W

The hydronic solver later determines:

flow rate
pipe pressure drop
pump head
emitter output
6. Hydronic Graph Invariants

To keep the network stable, enforce these rules:

1️⃣ Every edge must connect two valid nodes.

edge.start_node_id ∈ nodes
edge.end_node_id ∈ nodes

2️⃣ Node IDs must be unique.

3️⃣ Edges must not form isolated segments.

4️⃣ Flow paths must eventually reach a plant node (boiler / heat source).

7. Example Minimal Network

Example simple system:

nodes:
    boiler
    pump
    rad_A
    rad_B

edges:
    pipe_1: boiler → pump
    pipe_2: pump → rad_A
    pipe_3: rad_A → rad_B
    pipe_4: rad_B → boiler

This forms a loop.

8. Development Phases
Phase H1 — Graph Definition

Implement:

HydronicNode
HydronicEdge
HydronicGraph

No calculations.

Phase H2 — Network Validation

Add checks:

disconnected nodes
broken loops
duplicate edges
Phase H3 — Hydraulic Solver

Introduce physics:

flow rate
pressure drop
pipe friction
pump curve
Phase H4 — Thermal Coupling

Connect to heat-loss model:

room load → emitter → flow demand
9. Architectural Rule

Thermal and hydronic graphs must interact only through data, not structure.

Thermal graph → produces room loads
Hydronic graph → consumes room loads

No direct geometry modifications.

10. Resulting HVACgooee Architecture
Geometry
   ↓
Topology
   ↓
Thermal Graph
   ↓
Room Loads
   ↓
Emitters
   ↓
Hydronic Graph
   ↓
Hydraulic Solver
11. Why This Bootstrap is Important

This structure ensures:

clear graph topology
stable solver development
future expansion (valves, balancing, pumps)
clean coupling with thermal model

If you'd like, I can also show you something that will help a lot when you reach hydronics:

the three hydronic graph invariants that prevent almost every pipe-network bug (they’re the equivalent of the adjacency invariants we discussed earlier).
