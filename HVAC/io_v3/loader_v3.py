# ======================================================================
# HVAC/io_v3/loader_v3.py
# ======================================================================

"""
Project Loader v3
"""

from __future__ import annotations

from HVAC_legacy.io_v3.serializer_v3 import project_from_dict
from HVAC_legacy.io_v3.formats.json_v3 import load_json
from HVAC_legacy.project_v3.model_v3 import ProjectModelV3


def load_project_v3(path: str) -> ProjectModelV3:
    data = load_json(path)

    schema = data.get("schema_version", "unknown")
    if schema != "3.1":
        from HVAC_legacy.io_v3.migration_v3 import migrate_to_v3
        data = migrate_to_v3(data)

    return project_from_dict(data)
