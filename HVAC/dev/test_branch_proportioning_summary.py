# ======================================================================
# HVAC/dev/test_branch_proportioning_summary.py
# ======================================================================

from __future__ import annotations

import json
from pathlib import Path

from HVAC.project.project_state import ProjectState
from HVAC.hydronics.proportioning.branch_proportioning_summary_v1 import (
    build_branch_proportioning_summary_v1,
)


PROJECT_PATH = Path("HVAC/HVACprojects/6 room/project.json")


def make_dev_project_state() -> ProjectState:
    with PROJECT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return ProjectState.from_dict(data)


def main() -> None:
    project = make_dev_project_state()

    rows = build_branch_proportioning_summary_v1(project)

    print()
    print("=" * 96)
    print("HVACgooee — H-R1 Branch / Proportioning Summary")
    print("=" * 96)
    print()

    print(
        f"{'Group':<30} | "
        f"{'Role':<28} | "
        f"{'From':<24} | "
        f"{'To':<30} | "
        f"{'Flow':<12} | "
        f"{'Basis':<36} | "
        f"{'Status'}"
    )

    print("-" * 180)

    for row in rows:
        print(
            f"{row.group:<30} | "
            f"{row.role:<28} | "
            f"{row.from_label:<24} | "
            f"{row.to_label:<30} | "
            f"{row.flow_label:<12} | "
            f"{row.basis:<36} | "
            f"{row.status}"
        )


if __name__ == "__main__":
    main()