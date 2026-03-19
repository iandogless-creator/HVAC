from pathlib import Path
import json
import tempfile
import os
import hashlib
from HVAC.project.project_state import ProjectState
from .checksum import compute_checksum

MAX_BACKUPS = 3

def save(project_state: ProjectState, project_dir: Path) -> None:
    project_dir = project_dir.resolve()
    project_dir.mkdir(parents=True, exist_ok=True)

    _rotate_backups(project_dir)

    target_file = project_dir / "project.json"
    temp_file = None

    payload = project_state.to_dict()

    wrapper = {
        "schema_version": 4,
        "checksum": _compute_checksum(payload),
        "payload": payload,
    }

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=project_dir,
        ) as tmp:
            json.dump(wrapper, tmp, indent=4, sort_keys=True)
            temp_file = Path(tmp.name)

        os.replace(temp_file, target_file)

    finally:
        if temp_file and temp_file.exists():
            temp_file.unlink(missing_ok=True)


def _rotate_backups(project_dir: Path) -> None:
    """
    Rotate project.json backups safely.

    project.json
        → project.backup.1.json
        → project.backup.2.json
        → project.backup.3.json
    """

    project_file = project_dir / "project.json"

    if not project_file.exists():
        return

    # Remove oldest backup
    oldest = project_dir / f"project.backup.{MAX_BACKUPS}.json"
    if oldest.exists():
        oldest.unlink()

    # Shift existing backups up
    for i in range(MAX_BACKUPS - 1, 0, -1):
        src = project_dir / f"project.backup.{i}.json"
        dst = project_dir / f"project.backup.{i + 1}.json"
        if src.exists():
            os.replace(src, dst)

    # Move current project.json to backup.1
    first_backup = project_dir / "project.backup.1.json"
    os.replace(project_file, first_backup)

def _compute_checksum(payload: dict) -> str:
    """
    Deterministic SHA-256 checksum of payload.
    """
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()