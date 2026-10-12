"""The established job-folder root, relative to the installed HVAC package."""
from pathlib import Path


def default_project_root_v1() -> Path:
    return Path(__file__).resolve().parents[2] / "HVACprojects"
