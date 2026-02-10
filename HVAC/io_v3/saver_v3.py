# ======================================================================
# HVAC/io_v3/saver_v3.py
# ======================================================================

"""
Project Saver v3
"""

from __future__ import annotations

from HVAC.io_v3.serializer_v3 import project_to_dict
from HVAC.io_v3.formats.json_v3 import save_json
from HVAC.project_v3.model_v3 import ProjectModelV3


def save_project_v3(project: ProjectModelV3, path: str) -> None:
    data = project_to_dict(project)
    save_json(path, data)
