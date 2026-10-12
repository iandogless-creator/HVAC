"""Load a fresh, unsaved copy of the bundled 20-room example."""
from pathlib import Path
from uuid import uuid4
from HVAC.project.project_state import ProjectState
from HVAC.project_v3.persistence.loader import load as load_project

SAMPLE_NAME = "HVACgooee — 20-room example"


def sample_project_path_v1() -> Path:
    return Path(__file__).resolve().parents[2] / "examples" / "twenty_room_multileg_v1" / "project.json"


def make_sample_project_state_v1() -> ProjectState:
    project = load_project(sample_project_path_v1())
    project.project_id = str(uuid4())
    project.name = SAMPLE_NAME
    # Save must ask for the user's copy folder, never write into the bundled asset.
    project.project_dir = None
    return project
