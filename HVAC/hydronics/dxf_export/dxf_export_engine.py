"""
HVACgooee — BIM/DXF Export Engine (Core v1)
==========================================

Purpose
-------
Minimal but functional DXF writer for HVACgooee.

Produces a proper AutoCAD DXF file containing:
• Layers
• Points (nodes)
• Lines (pipes)
• Text labels (node IDs)
• Optional colours per layer

Inputs
------
• nodes: {id: (x, y)}
• segments: [(id1, id2)]
• layer visibility + colours (from UI)
• scale and basepoint options

No GUI or file dialogs here.
Pure backend. Safe to call from any part of the system.

DXF Version
-----------
AC1009 (R12 / 2000 compatible) — simplest and most portable.

"""


from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional


Point = Tuple[float, float]
Segment = Tuple[str, str]


# ---------------------------------------------------------------------------
# Layer Definition
# ---------------------------------------------------------------------------

@dataclass
class DxfLayer:
    name: str
    color: int = 7     # AutoCAD color index (7 = white)
    visible: bool = True


# ---------------------------------------------------------------------------
# Export Configuration
# ---------------------------------------------------------------------------

@dataclass
class DxfExportConfig:
    """
    Controls scaling, offsets, and layer mapping.
    """
    scale: float = 100.0       # world units → DXF units (mm or arbitrary)
    offset_x: float = 0.0
    offset_y: float = 0.0

    # which layers exist with colour + visibility
    layers: Dict[str, DxfLayer] = field(default_factory=dict)

    # export text labels?
    export_labels: bool = True


# ---------------------------------------------------------------------------
# DXF Engine
# ---------------------------------------------------------------------------

class DxfExportEngine:
    """
    Generates a DXF string from nodes + segments and layer definitions.
    """

    def __init__(self, config: Optional[DxfExportConfig] = None):
        self.cfg = config or DxfExportConfig()

    # ------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------

    def _to_dxf_coord(self, p: Point) -> Tuple[float, float]:
        """Apply scale + offsets to a point."""
        x = p[0] * self.cfg.scale + self.cfg.offset_x
        y = p[1] * self.cfg.scale + self.cfg.offset_y
        return x, y

    # ------------------------------------------------------------
    # DXF Builders
    # ------------------------------------------------------------

    def _header(self) -> str:
        """Return DXF HEADER + TABLE setup."""
        lines = []
        lines += ["0", "SECTION", "2", "HEADER", "0", "ENDSEC"]
        lines += ["0", "SECTION", "2", "TABLES"]

        # LAYER TABLE
        lines += ["0", "TABLE", "2", "LAYER"]
        for layer in self.cfg.layers.values():
            lines += [
                "0", "LAYER",
                "2", layer.name,
                "70", "0",
                "62", str(layer.color if layer.visible else 0),  # 0 = off
                "6", "CONTINUOUS",
            ]
        lines += ["0", "ENDTAB"]
        lines += ["0", "ENDSEC"]

        # ENTITIES
        lines += ["0", "SECTION", "2", "ENTITIES"]
        return "\n".join(lines)

    def _footer(self) -> str:
        return "\n".join(["0", "ENDSEC", "0", "EOF"])

    # ------------------------------------------------------------
    # Entities
    # ------------------------------------------------------------

    def _dxf_line(self, start: Point, end: Point, layer: str) -> str:
        sx, sy = self._to_dxf_coord(start)
        ex, ey = self._to_dxf_coord(end)
        return "\n".join([
            "0", "LINE",
            "8", layer,
            "10", f"{sx}",
            "20", f"{sy}",
            "30", "0",
            "11", f"{ex}",
            "21", f"{ey}",
            "31", "0",
        ])

    def _dxf_point(self, p: Point, layer: str) -> str:
        x, y = self._to_dxf_coord(p)
        return "\n".join([
            "0", "POINT",
            "8", layer,
            "10", f"{x}",
            "20", f"{y}",
            "30", "0",
        ])

    def _dxf_text(self, p: Point, text: str, layer: str) -> str:
        x, y = self._to_dxf_coord(p)
        return "\n".join([
            "0", "TEXT",
            "8", layer,
            "10", f"{x}",
            "20", f"{y}",
            "30", "0",
            "40", "20",        # text height
            "1", text,
        ])

    # ------------------------------------------------------------
    # Main Exporter
    # ------------------------------------------------------------

    def export_dxf(
        self,
        nodes: Dict[str, Point],
        segments: List[Segment],
    ) -> str:
        """
        Create a complete DXF string.

        Very simple logic:
        - Pipes → layer "PIPES"
        - Nodes → layer "NODES"
        - Text → layer "TEXT" (if enabled)

        In v1, we assume layers already exist in config.
        """

        # Start with header + tables
        out = [self._header()]

        # --------------------------------------------------------
        # Draw segments (pipes)
        # --------------------------------------------------------
        if "PIPES" in self.cfg.layers and self.cfg.layers["PIPES"].visible:
            for a, b in segments:
                if a in nodes and b in nodes:
                    out.append(
                        self._dxf_line(nodes[a], nodes[b], "PIPES")
                    )

        # --------------------------------------------------------
        # Draw nodes
        # --------------------------------------------------------
        if "NODES" in self.cfg.layers and self.cfg.layers["NODES"].visible:
            for nid, p in nodes.items():
                out.append(
                    self._dxf_point(p, "NODES")
                )

        # --------------------------------------------------------
        # Draw text labels
        # --------------------------------------------------------
        if self.cfg.export_labels and "TEXT" in self.cfg.layers and self.cfg.layers["TEXT"].visible:
            for nid, p in nodes.items():
                out.append(
                    self._dxf_text((p[0] + 0.02, p[1] + 0.02), nid, "TEXT")
                )

        # Footer
        out.append(self._footer())
        return "\n".join(out)
