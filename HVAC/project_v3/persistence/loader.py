from pathlib import Path
import json

from HVAC.project.project_state import ProjectState
from .saver import compute_checksum

from HVAC.project.project_state import ProjectState

MAX_BACKUPS = 5


# ----------------------------------------------------------------------
# Internal validation
# ----------------------------------------------------------------------
def _load_and_validate(file_path: Path) -> dict:
    with file_path.open("r", encoding="utf-8") as f:
        wrapper = json.load(f)
    return wrapper
#    if wrapper.get("schema_version") != 4:
 #       raise ValueError("Unsupported schema version")

    #payload = wrapper.get("payload")
    #checksum = wrapper.get("checksum")

    #if not isinstance(payload, dict) or not isinstance(checksum, str):
     #   raise ValueError("Invalid project file structure")

    #computed = compute_checksum(payload)

    #if computed != checksum:
     #   raise ValueError("Checksum mismatch")

#    return payload

def _unwrap_project_payload(data: dict) -> dict:
    payload = data

    while (
        isinstance(payload, dict)
        and "project_id" not in payload
        and isinstance(payload.get("payload"), dict)
    ):
        payload = payload["payload"]

    return payload



# ----------------------------------------------------------------------
# Backup restoration
# ----------------------------------------------------------------------
def _restore_backup(backup_path: Path, main_path: Path) -> None:
    main_path.write_bytes(backup_path.read_bytes())


# ----------------------------------------------------------------------
# Public loader
# ----------------------------------------------------------------------
def load(project_path: Path) -> ProjectState:
    """
    Load an HVACgooee project.

    Accepts either:
        project folder/
        project folder/project.json
    """

    project_path = Path(project_path).resolve()

    if project_path.is_dir():
        project_file = project_path / "project.json"
        project_dir = project_path
    else:
        project_file = project_path
        project_dir = project_path.parent

    if not project_file.exists():
        raise FileNotFoundError(f"Project file not found: {project_file}")

    with project_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    payload = _unwrap_project_payload(data)

    if "project_id" not in payload:
        raise ValueError(
            f"Invalid HVACgooee project file: missing project_id in {project_file}"
        )

    project_state = ProjectState.from_dict(payload)
    project_state.project_dir = project_dir

    return project_state