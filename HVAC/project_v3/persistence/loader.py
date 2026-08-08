from __future__ import annotations

import hmac
import json
from pathlib import Path
from typing import Any

from HVAC.project.project_state import ProjectState
from .checksum import compute_checksum


SUPPORTED_WRAPPER_SCHEMA_VERSIONS = frozenset({4})


# ----------------------------------------------------------------------
# Internal validation
# ----------------------------------------------------------------------
def _load_and_validate(file_path: Path) -> dict:
    """Return one validated ProjectState payload from ``file_path``."""

    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid HVACgooee project JSON in {file_path}: {exc.msg}"
        ) from exc

    return _validated_project_payload(data, file_path=file_path)


def _validated_project_payload(data: Any, *, file_path: Path) -> dict:
    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid HVACgooee project file structure in {file_path}"
        )

    # Authentic legacy files persisted ProjectState directly. ProjectState
    # performs their payload-schema validation in from_dict().
    if "project_id" in data:
        if "payload" in data or "checksum" in data:
            raise ValueError(
                f"Ambiguous HVACgooee project file structure in {file_path}"
            )
        return data

    schema_version = data.get("schema_version")
    if schema_version not in SUPPORTED_WRAPPER_SCHEMA_VERSIONS:
        raise ValueError(
            "Unsupported HVACgooee project wrapper schema version "
            f"{schema_version!r} in {file_path}"
        )

    payload = data.get("payload")
    checksum = data.get("checksum")
    if (
        not isinstance(payload, dict)
        or not isinstance(checksum, str)
        or not checksum
    ):
        raise ValueError(
            f"Invalid HVACgooee project wrapper structure in {file_path}"
        )

    computed_checksum = compute_checksum(payload)
    if not hmac.compare_digest(computed_checksum, checksum):
        raise ValueError(f"HVACgooee project checksum mismatch in {file_path}")

    if "project_id" not in payload:
        raise ValueError(
            f"Invalid HVACgooee project payload: missing project_id in {file_path}"
        )

    return payload


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

    payload = _load_and_validate(project_file)

    if "project_id" not in payload:
        raise ValueError(
            f"Invalid HVACgooee project file: missing project_id in {project_file}"
        )

    project_state = ProjectState.from_dict(payload)
    project_state.project_dir = project_dir

    return project_state