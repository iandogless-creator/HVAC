# ======================================================================
# HVAC/io_v3/migration_v3.py
# ======================================================================

"""
Project Migration v3

LOCKED:
• Stateless
• Dict → Dict
"""

from __future__ import annotations
from typing import Dict, Any


def migrate_to_v3(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for legacy project → v3 migration.

    For now: hard fail or shallow map.
    """
    raise NotImplementedError("Project schema migration not yet implemented.")
