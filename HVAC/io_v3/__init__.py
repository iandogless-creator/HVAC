# ======================================================================
# HVAC/io_v3/__init__.py
# ======================================================================

"""
HVACgooee — IO v3 (CANONICAL)

LOCKED:
• Translates ProjectModelV3 to/from external representations
• No calculations
• No validation logic
• No engine imports
"""

from .loader_v3 import load_project_v3
from .saver_v3 import save_project_v3

__all__ = ["load_project_v3", "save_project_v3"]
