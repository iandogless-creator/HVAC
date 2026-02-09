"""
HVACgooee — DXF Export System v1 (Hydronic Networks)
====================================================

Purpose
-------
Minimal, dependency-free DXF (ASCII) writer for exporting:

- Hydronic network nodes
- Hydronic pipe segments
- Simple text labels

This is the first DXF export layer, focused on hydronics only:

DXF Layers:
    - HVAC-NODES : node points (plant, legs, sublegs, emitters, etc.)
    - HVAC-PIPES : pipe centre-lines between nodes
    - HVAC-TEXT  : node IDs and simple labels

Design Rules
------------
- NO GUI code in this module.
- NO DXF parsing or heavy BIM logic (that's for later).
- Keep it generic: other subsystems can reuse the DXF writer.
- Caller is responsible for writing the returned DXF string to disk.

Inputs from network layout generator
------------------------------------
We expect the hydronic network layout generator to provide:

    nodes: Dict[str, Tuple[float, float]]
        Mapping: node_id → (x_m, y_m) in metres (logical coordinates)

    segments: List[Tuple[str, str]]
        Sequence of (node_id_start, node_id_end) pairs, forming polylines.

The export function scales metres → DXF units (default: mm).

Typical use
-----------
    dxf_str = export_hydronic_network_to_dxf(nodes, segments, config=None)
    with open("network.dxf", "w", encoding="utf-8") as f:
        f.write(dxf_str)

Future extensions
-----------------
- More layers (HVAC-ROOMS, HVAC-WINDOWS, HVAC-SYMBOLS)
- Block definitions for symbols
- BIM tagging (Room IDs, system IDs, etc.)
"""

from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional


# ---------------------------------------------------------------------------
# DXF Export Configuration
# ---------------------------------------------------------------------------

@dataclass
class DxfExportConfig:
    """
    Configuration for DXF hydronic export.
    """
    units: str = "mm"                 # Drawing units (DXF itself is unit-less)
    scale_m_to_units: float = 1000.0  # metres → drawing units (1m = 1000mm)

    layer_nodes: str = "HVAC-NODES"
    layer_pipes: str = "HVAC-PIPES"
    layer_text: str = "HVAC-TEXT"

    node_color: int = 2               # AutoCAD index (2 = Yellow)
    pipe_color: int = 4               # 4 = Cyan
    text_color: int = 7               # 7 = White

    text_height: float = 2.5          # text height in drawing units
    text_offset_x: float = 5.0        # label offset from node
    text_offset_y: float = 5.0

    add_node_labels: bool = True      # write node IDs as TEXT


# ---------------------------------------------------------------------------
# Minimal DXF Writer
# ---------------------------------------------------------------------------

class DxfWriter:
    """
    Ultra-lightweight ASCII DXF writer (R12-style).

    Supports:
    - HEADER (minimal)
    - TABLES → LAYER table
    - ENTITIES → LINE, POINT, TEXT

    Not a full DXF implementation, just enough for Gooee v1 exports.
    """

    def __init__(self, config: Optional[DxfExportConfig] = None):
        self.config = config or DxfExportConfig()
        self.layers = {}          # name → (color, linetype)
        self.entities: List[str] = []

    # ----- Low-level helpers ------------------------------------------------

    @staticmethod
    def _pair(code: int, value) -> str:
        return f"{code}\n{value}\n"

    # ----- Layer Management -------------------------------------------------

    def add_layer(self, name: str, color: int = 7, linetype: str = "CONTINUOUS") -> None:
        """
        Register a layer to be written into the TABLES section.
        """
        if name not in self.layers:
            self.layers[name] = (color, linetype)

    def ensure_default_layers(self) -> None:
        """
        Ensure our standard hydronic layers exist.
        """
        self.add_layer(self.config.layer_nodes, self.config.node_color)
        self.add_layer(self.config.layer_pipes, self.config.pipe_color)
        self.add_layer(self.config.layer_text, self.config.text_color)

    # ----- Entity Creation --------------------------------------------------

    def add_line(self, x1: float, y1: float, x2: float, y2: float, layer: str) -> None:
        """
        Add a LINE entity.
        """
        e = []
        e.append(self._pair(0, "LINE"))
        e.append(self._pair(8, layer))
        e.append(self._pair(10, x1))
        e.append(self._pair(20, y1))
        e.append(self._pair(30, 0.0))
        e.append(self._pair(11, x2))
        e.append(self._pair(21, y2))
        e.append(self._pair(31, 0.0))
        self.entities.append("".join(e))

    def add_point(self, x: float, y: float, layer: str) -> None:
        """
        Add a POINT entity representing a node centre.
        """
        e = []
        e.append(self._pair(0, "POINT"))
        e.append(self._pair(8, layer))
        e.append(self._pair(10, x))
        e.append(self._pair(20, y))
        e.append(self._pair(30, 0.0))
        self.entities.append("".join(e))

    def add_text(self, x: float, y: float, text: str, layer: str, height: Optional[float] = None) -> None:
        """
        Add a simple TEXT entity.
        """
        if height is None:
            height = self.config.text_height

        e = []
        e.append(self._pair(0, "TEXT"))
        e.append(self._pair(8, layer))
        e.append(self._pair(10, x))
        e.append(self._pair(20, y))
        e.append(self._pair(30, 0.0))
        e.append(self._pair(40, height))
        e.append(self._pair(1, text))
        self.entities.append("".join(e))

    # ----- Document Assembly -----------------------------------------------

    def _build_header_section(self) -> str:
        """
        Minimal HEADER section (can be expanded later if needed).
        """
        parts = []
        parts.append(self._pair(0, "SECTION"))
        parts.append(self._pair(2, "HEADER"))
        # Placeholder: we could write $INSUNITS, $EXTMIN, $EXTMAX here later.
        parts.append(self._pair(0, "ENDSEC"))
        return "".join(parts)

    def _build_tables_section(self) -> str:
        """
        Build TABLES section with a LAYER table.
        """
        parts = []
        parts.append(self._pair(0, "SECTION"))
        parts.append(self._pair(2, "TABLES"))

        # LAYER table
        parts.append(self._pair(0, "TABLE"))
        parts.append(self._pair(2, "LAYER"))
        parts.append(self._pair(70, len(self.layers)))

        for name, (color, linetype) in self.layers.items():
            parts.append(self._pair(0, "LAYER"))
            parts.append(self._pair(2, name))
            parts.append(self._pair(70, 0))          # flags
            parts.append(self._pair(62, color))      # color index
            parts.append(self._pair(6, linetype))    # linetype name

        parts.append(self._pair(0, "ENDTAB"))

        parts.append(self._pair(0, "ENDSEC"))
        return "".join(parts)

    def _build_entities_section(self) -> str:
        parts = []
        parts.append(self._pair(0, "SECTION"))
        parts.append(self._pair(2, "ENTITIES"))

        for e in self.entities:
            parts.append(e)

        parts.append(self._pair(0, "ENDSEC"))
        return "".join(parts)

    def to_string(self) -> str:
        """
        Construct the full DXF file as a single string.
        """
        self.ensure_default_layers()

        parts = []
        parts.append(self._pair(0, "SECTION"))   # just to be safe, but HEADER builder starts its own
        # Actually we rely on dedicated builders:
        parts = []  # reset

        parts.append(self._build_header_section())
        parts.append(self._build_tables_section())
        parts.append(self._build_entities_section())
        parts.append(self._pair(0, "EOF"))

        return "".join(parts)


# ---------------------------------------------------------------------------
# Hydronic Network DXF Export
# ---------------------------------------------------------------------------

def export_hydronic_network_to_dxf(
    nodes: Dict[str, Tuple[float, float]],
    segments: List[Tuple[str, str]],
    config: Optional[DxfExportConfig] = None,
) -> str:
    """
    Convert a hydronic network layout into a DXF string.

    Parameters
    ----------
    nodes:
        Mapping of node_id → (x_m, y_m) in metres, as produced by
        the hydronic network layout generator.
    segments:
        List of (node_id_start, node_id_end) tuples describing pipes
        between nodes.
    config:
        Optional DxfExportConfig. If None, defaults are used.

    Returns
    -------
    dxf_string:
        A complete ASCII DXF file ready to be written to disk.

    Notes
    -----
    - Coordinates are scaled from metres to drawing units using
      config.scale_m_to_units (default: mm).
    - Nodes are output as POINT entities on HVAC-NODES.
    - Pipes are output as LINE entities on HVAC-PIPES.
    - Node IDs are written as TEXT on HVAC-TEXT (unless disabled).
    """
    cfg = config or DxfExportConfig()
    writer = DxfWriter(cfg)

    scale = cfg.scale_m_to_units

    # Add entities for nodes
    for node_id, (x_m, y_m) in nodes.items():
        x = x_m * scale
        y = y_m * scale

        writer.add_point(x, y, cfg.layer_nodes)

        if cfg.add_node_labels:
            writer.add_text(
                x + cfg.text_offset_x,
                y + cfg.text_offset_y,
                node_id,
                cfg.layer_text,
                cfg.text_height,
            )

    # Add entities for pipe segments
    for start_id, end_id in segments:
        if start_id not in nodes or end_id not in nodes:
            # We deliberately ignore segments with missing nodes
            # rather than raising, to keep export robust.
            continue

        (x1_m, y1_m) = nodes[start_id]
        (x2_m, y2_m) = nodes[end_id]

        x1 = x1_m * scale
        y1 = y1_m * scale
        x2 = x2_m * scale
        y2 = y2_m * scale

        writer.add_line(x1, y1, x2, y2, cfg.layer_pipes)

    return writer.to_string()
