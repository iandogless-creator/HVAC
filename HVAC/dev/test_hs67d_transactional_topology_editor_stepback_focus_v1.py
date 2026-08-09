from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)
from HVAC.hydronics.topology.canonical_topology_validation_migration_v1 import (
    migrate_legacy_flat_sublegs_to_canonical_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import HydronicTopologyV1
from HVAC.hydronics.topology.transactional_topology_editor_v1 import (
    FOCUS_BRANCH_SUBLEG,
    FOCUS_LEG,
    MAX_TOPOLOGY_STEPBACKS,
    TOPOLOGY_STEPBACK_DIRECTORY,
    commit_validated_topology_candidate_v1,
    load_latest_topology_stepback_candidate_v1,
)
from HVAC.project_v3.persistence.loader import load


def main() -> None:
    with TemporaryDirectory(prefix="hs67d-") as temporary_directory:
        project_dir = Path(temporary_directory)
        project = build_hydronic_20_room_multileg_project_v1()
        project.project_dir = project_dir
        project.hydronics_valid = True
        original_dict = project.hydronic_topology.to_dict()

        migration = migrate_legacy_flat_sublegs_to_canonical_v1(
            project.hydronic_topology,
            known_room_ids=project.rooms,
        )
        assert migration.ready and migration.topology is not None

        result = commit_validated_topology_candidate_v1(
            project,
            migration.topology,
            action_label="Migrate legacy flat branches",
            focus_kind=FOCUS_BRANCH_SUBLEG,
            focus_target_id="leg-001-subleg-b",
            created_at_utc="2026-08-08T20:00:00+00:00",
        )
        assert result.ready, result.blockers
        assert result.changed
        assert result.downstream_stale
        assert result.stepback_path is not None
        assert result.stepback_path.is_file()
        assert result.focus is not None
        assert result.focus.kind == FOCUS_BRANCH_SUBLEG
        assert result.focus.leg_id == "leg-001"
        assert result.focus.subleg_id == "leg-001-subleg-b"
        assert not project.hydronics_valid
        assert len(project.hydronic_topology.legs[0].sublegs) == 1

        # The durable full-state snapshot is the exact pre-change ProjectState.
        pre_change = load(result.stepback_path)
        assert pre_change.hydronic_topology.to_dict() == original_dict
        assert pre_change.hydronics_valid

        restore = load_latest_topology_stepback_candidate_v1(project_dir)
        assert restore.ready, restore.blockers
        assert restore.project_state is not None
        assert restore.project_state is not project
        assert restore.project_state.project_dir == project_dir.resolve()
        assert restore.project_state.hydronic_topology.to_dict() == original_dict
        assert restore.action_label == "Migrate legacy flat branches"
        assert restore.focus == result.focus

        # Invalid focus and invalid topology cannot write or mutate anything.
        current_dict = project.hydronic_topology.to_dict()
        before_paths = sorted(
            (project_dir / TOPOLOGY_STEPBACK_DIRECTORY).glob("*.json")
        )
        blocked_focus = commit_validated_topology_candidate_v1(
            project,
            HydronicTopologyV1.from_dict(current_dict),
            action_label="Bad focus",
            focus_kind=FOCUS_LEG,
            focus_target_id="missing-leg",
        )
        assert not blocked_focus.ready
        assert project.hydronic_topology.to_dict() == current_dict
        assert sorted(
            (project_dir / TOPOLOGY_STEPBACK_DIRECTORY).glob("*.json")
        ) == before_paths

        invalid_candidate = HydronicTopologyV1.from_dict(current_dict)
        invalid_candidate.legs[0].sublegs[0].origin_room_id = "wrong-origin"
        blocked_topology = commit_validated_topology_candidate_v1(
            project,
            invalid_candidate,
            action_label="Invalid topology",
        )
        assert not blocked_topology.ready
        assert project.hydronic_topology.to_dict() == current_dict

        # Fifty rotating snapshots remain ordered and independent of normal saves.
        for index in range(52):
            candidate = HydronicTopologyV1.from_dict(
                project.hydronic_topology.to_dict()
            )
            candidate.legs[0].label = f"Leg edit {index:02d}"
            rotated = commit_validated_topology_candidate_v1(
                project,
                candidate,
                action_label=f"Rename leg edit {index:02d}",
                focus_kind=FOCUS_LEG,
                focus_target_id="leg-001",
                created_at_utc=f"2026-08-08T20:{index:02d}:00+00:00",
            )
            assert rotated.ready and rotated.changed, rotated.blockers

        stepback_dir = project_dir / TOPOLOGY_STEPBACK_DIRECTORY
        paths = [
            stepback_dir / f"project.stepback.{index}.json"
            for index in range(1, MAX_TOPOLOGY_STEPBACKS + 1)
        ]
        assert all(path.is_file() for path in paths)
        assert not (stepback_dir / "project.stepback.51.json").exists()
        assert load(paths[0]).hydronic_topology.legs[0].label == "Leg edit 50"
        assert load(paths[-1]).hydronic_topology.legs[0].label == "Leg edit 01"

        # An unwritable step-back location blocks before live mutation.
        blocked_project = build_hydronic_20_room_multileg_project_v1()
        blocked_project.project_dir = project_dir / "blocked-project"
        blocked_project.project_dir.mkdir()
        (blocked_project.project_dir / TOPOLOGY_STEPBACK_DIRECTORY).write_text(
            "not a directory", encoding="utf-8"
        )
        blocked_original = blocked_project.hydronic_topology.to_dict()
        blocked_migration = migrate_legacy_flat_sublegs_to_canonical_v1(
            blocked_project.hydronic_topology,
            known_room_ids=blocked_project.rooms,
        )
        assert blocked_migration.ready and blocked_migration.topology is not None
        write_blocked = commit_validated_topology_candidate_v1(
            blocked_project,
            blocked_migration.topology,
            action_label="Must not install",
        )
        assert not write_blocked.ready
        assert blocked_project.hydronic_topology.to_dict() == blocked_original

    print(
        "OK — H-S67-D validated topology transactions create 50 rotating "
        "full-ProjectState step-backs and return exact focus evidence."
    )


if __name__ == "__main__":
    main()
