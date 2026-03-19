from pathlib import Path
import json

from HVAC.project.project_state import ProjectState
from .saver import compute_checksum

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


# ----------------------------------------------------------------------
# Backup restoration
# ----------------------------------------------------------------------
def _restore_backup(backup_path: Path, main_path: Path) -> None:
    main_path.write_bytes(backup_path.read_bytes())


# ----------------------------------------------------------------------
# Public loader
# ----------------------------------------------------------------------
def load(project_dir: Path) -> ProjectState:
    project_dir = project_dir.resolve()

    main_file = project_dir / "project.json"

    if not main_file.exists():
        raise FileNotFoundError("project.json not found")

    candidates = [main_file] + [
        project_dir / f"project.backup.{i}.json"
        for i in range(1, MAX_BACKUPS + 1)
    ]

    for file_path in candidates:
        if not file_path.exists():
            continue

        try:
            payload = _load_and_validate(file_path)

            # Recovery: promote backup to main
            if file_path != main_file:
                print(f"[RECOVERY] Restored from {file_path.name}")
                _restore_backup(file_path, main_file)

            return ProjectState.from_dict(payload)


        except Exception as e:

            raise
    raise ValueError("All project files corrupted — recovery failed")