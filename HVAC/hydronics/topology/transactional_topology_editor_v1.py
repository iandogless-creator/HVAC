from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from HVAC.hydronics.topology.canonical_topology_validation_migration_v1 import (
    validate_canonical_hydronic_topology_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import HydronicTopologyV1
from HVAC.hydronics.topology.recursive_subleg_contract_v1 import (
    BRANCH_SUBLEG_KIND,
    PRINCIPAL_SUBLEG_KIND,
    build_recursive_subleg_positions_v1,
)
from HVAC.project.project_state import ProjectState
from HVAC.project_v3.persistence.checksum import compute_checksum
from HVAC.project_v3.persistence.loader import load


MAX_TOPOLOGY_STEPBACKS = 50
TOPOLOGY_STEPBACK_DIRECTORY = "topology-stepbacks"
TOPOLOGY_STEPBACK_SCHEMA = "topology_project_stepback_v1"

FOCUS_TOPOLOGY = "topology"
FOCUS_LEG = "leg"
FOCUS_PRINCIPAL_SUBLEG = "principal_subleg"
FOCUS_BRANCH_SUBLEG = "branch_subleg"
FOCUS_ROOM = "room"
FOCUS_STAGING_ROOM = "staging_room"


@dataclass(frozen=True, slots=True)
class TopologyFocusEvidenceV1:
    kind: str
    target_id: str = ""
    leg_id: str = ""
    subleg_id: str = ""
    room_id: str = ""
    panel: str = "topology_arranger"
    status: str = "Topology focus unresolved"

    def to_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "target_id": self.target_id,
            "leg_id": self.leg_id,
            "subleg_id": self.subleg_id,
            "room_id": self.room_id,
            "panel": self.panel,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TopologyFocusEvidenceV1":
        return cls(
            kind=str(data.get("kind") or FOCUS_TOPOLOGY),
            target_id=str(data.get("target_id") or ""),
            leg_id=str(data.get("leg_id") or ""),
            subleg_id=str(data.get("subleg_id") or ""),
            room_id=str(data.get("room_id") or ""),
            panel=str(data.get("panel") or "topology_arranger"),
            status=str(data.get("status") or "Topology focus restored"),
        )


@dataclass(frozen=True, slots=True)
class TopologyTransactionResultV1:
    ready: bool
    changed: bool = False
    stepback_path: Path | None = None
    focus: TopologyFocusEvidenceV1 | None = None
    downstream_stale: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "Topology transaction not run"


@dataclass(frozen=True, slots=True)
class TopologyStepbackRestoreCandidateV1:
    ready: bool
    project_state: ProjectState | None = None
    stepback_path: Path | None = None
    action_label: str = ""
    focus: TopologyFocusEvidenceV1 | None = None
    blockers: tuple[str, ...] = ()
    status: str = "Topology step-back restore candidate not loaded"


def commit_validated_topology_candidate_v1(
    project_state: ProjectState,
    candidate_topology: HydronicTopologyV1,
    *,
    action_label: str,
    focus_kind: str = FOCUS_TOPOLOGY,
    focus_target_id: str = "",
    created_at_utc: str | None = None,
) -> TopologyTransactionResultV1:
    """Install one complete topology candidate after a full step-back succeeds."""

    if not isinstance(project_state, ProjectState):
        return _transaction_blocked("ProjectState is required")
    if not isinstance(candidate_topology, HydronicTopologyV1):
        return _transaction_blocked("HydronicTopologyV1 candidate is required")

    action = str(action_label or "").strip()
    if not action:
        return _transaction_blocked("Topology action label is required")

    try:
        candidate_copy = HydronicTopologyV1.from_dict(
            candidate_topology.to_dict()
        )
    except (RecursionError, TypeError, ValueError) as exc:
        return _transaction_blocked(f"Topology candidate cannot be copied: {exc}")

    validation = validate_canonical_hydronic_topology_v1(
        candidate_copy,
        known_room_ids=project_state.rooms,
    )
    if not validation.ready:
        return _transaction_blocked(
            *validation.blockers,
            warnings=validation.warnings,
        )

    focus = _resolve_focus(
        candidate_copy,
        kind=focus_kind,
        target_id=focus_target_id,
        known_room_ids=project_state.rooms,
    )
    if focus is None:
        return _transaction_blocked(
            f"Topology focus target is unavailable: {focus_kind}/{focus_target_id}"
        )

    current_topology = project_state.hydronic_topology
    if (
        isinstance(current_topology, HydronicTopologyV1)
        and current_topology.to_dict() == candidate_copy.to_dict()
    ):
        return TopologyTransactionResultV1(
            ready=True,
            changed=False,
            focus=focus,
            warnings=validation.warnings,
            status="Ready — topology candidate is unchanged; no step-back created",
        )

    project_dir = _project_directory(project_state)
    if project_dir is None:
        return _transaction_blocked(
            "Saved project directory is required before topology editing"
        )

    timestamp = str(created_at_utc or "").strip() or datetime.now(
        timezone.utc
    ).isoformat()
    try:
        stepback_path = _write_topology_stepback_v1(
            project_state,
            project_dir=project_dir,
            action_label=action,
            focus=focus,
            created_at_utc=timestamp,
        )
    except (OSError, TypeError, ValueError) as exc:
        return _transaction_blocked(
            f"Topology step-back could not be written; live state unchanged: {exc}"
        )

    # The only live-state mutation occurs after validation and durable snapshot.
    project_state.hydronic_topology = candidate_copy
    project_state.hydronics_valid = False

    return TopologyTransactionResultV1(
        ready=True,
        changed=True,
        stepback_path=stepback_path,
        focus=focus,
        downstream_stale=True,
        warnings=validation.warnings,
        status=(
            "Ready — validated topology installed after full ProjectState "
            "step-back; downstream hydronic evidence is stale"
        ),
    )


def load_latest_topology_stepback_candidate_v1(
    project_dir: Path,
) -> TopologyStepbackRestoreCandidateV1:
    """Load the newest valid step-back as a separate ProjectState candidate."""

    root = Path(project_dir).resolve()
    stepback_path = root / TOPOLOGY_STEPBACK_DIRECTORY / "project.stepback.1.json"
    if not stepback_path.is_file():
        return _restore_blocked("No topology step-back is available")

    try:
        wrapper = json.loads(stepback_path.read_text(encoding="utf-8"))
        if wrapper.get("snapshot_kind") != TOPOLOGY_STEPBACK_SCHEMA:
            return _restore_blocked("Newest file is not a topology step-back")
        metadata = wrapper.get("stepback_metadata")
        if not isinstance(metadata, dict):
            return _restore_blocked("Topology step-back metadata is missing")
        restored = load(stepback_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _restore_blocked(f"Topology step-back is invalid: {exc}")

    restored.project_dir = root
    focus_data = metadata.get("focus")
    focus = (
        TopologyFocusEvidenceV1.from_dict(focus_data)
        if isinstance(focus_data, dict)
        else TopologyFocusEvidenceV1(
            kind=FOCUS_TOPOLOGY,
            status="Topology focus restored",
        )
    )
    return TopologyStepbackRestoreCandidateV1(
        ready=True,
        project_state=restored,
        stepback_path=stepback_path,
        action_label=str(metadata.get("action_label") or ""),
        focus=focus,
        status="Ready — newest topology step-back loaded as a restore candidate",
    )


def _write_topology_stepback_v1(
    project_state: ProjectState,
    *,
    project_dir: Path,
    action_label: str,
    focus: TopologyFocusEvidenceV1,
    created_at_utc: str,
) -> Path:
    stepback_dir = project_dir / TOPOLOGY_STEPBACK_DIRECTORY
    stepback_dir.mkdir(parents=True, exist_ok=True)

    payload = project_state.to_dict()
    wrapper = {
        "schema_version": 4,
        "checksum": compute_checksum(payload),
        "payload": payload,
        "snapshot_kind": TOPOLOGY_STEPBACK_SCHEMA,
        "stepback_metadata": {
            "action_label": action_label,
            "created_at_utc": created_at_utc,
            "focus": focus.to_dict(),
        },
    }

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".project.stepback.",
        suffix=".tmp",
        dir=stepback_dir,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            json.dump(wrapper, handle, indent=4, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())

        oldest = stepback_dir / f"project.stepback.{MAX_TOPOLOGY_STEPBACKS}.json"
        oldest.unlink(missing_ok=True)
        for index in range(MAX_TOPOLOGY_STEPBACKS - 1, 0, -1):
            source = stepback_dir / f"project.stepback.{index}.json"
            destination = stepback_dir / f"project.stepback.{index + 1}.json"
            if source.exists():
                os.replace(source, destination)

        target = stepback_dir / "project.stepback.1.json"
        os.replace(temporary_path, target)
        return target
    finally:
        temporary_path.unlink(missing_ok=True)


def _resolve_focus(
    topology: HydronicTopologyV1,
    *,
    kind: str,
    target_id: str,
    known_room_ids: Any = (),
) -> TopologyFocusEvidenceV1 | None:
    clean_kind = str(kind or "").strip()
    clean_target = str(target_id or "").strip()
    if clean_kind == FOCUS_TOPOLOGY:
        return TopologyFocusEvidenceV1(
            kind=FOCUS_TOPOLOGY,
            status="Focus complete topology",
        )

    if clean_kind == FOCUS_LEG:
        if any(leg.leg_id == clean_target for leg in topology.legs):
            return TopologyFocusEvidenceV1(
                kind=FOCUS_LEG,
                target_id=clean_target,
                leg_id=clean_target,
                status=f"Focus leg {clean_target}",
            )
        return None

    positions = build_recursive_subleg_positions_v1(topology)
    if clean_kind in {FOCUS_PRINCIPAL_SUBLEG, FOCUS_BRANCH_SUBLEG}:
        required_kind = (
            PRINCIPAL_SUBLEG_KIND
            if clean_kind == FOCUS_PRINCIPAL_SUBLEG
            else BRANCH_SUBLEG_KIND
        )
        position = next(
            (
                row
                for row in positions
                if row.subleg_id == clean_target and row.kind == required_kind
            ),
            None,
        )
        if position is None:
            return None
        return TopologyFocusEvidenceV1(
            kind=clean_kind,
            target_id=clean_target,
            leg_id=position.leg_id,
            subleg_id=clean_target,
            status=f"Focus {clean_kind.replace('_', ' ')} {clean_target}",
        )

    if clean_kind == FOCUS_ROOM:
        for position in positions:
            if clean_target in {str(room_id) for room_id in position.subleg.route_room_ids}:
                return TopologyFocusEvidenceV1(
                    kind=FOCUS_ROOM,
                    target_id=clean_target,
                    leg_id=position.leg_id,
                    subleg_id=position.subleg_id,
                    room_id=clean_target,
                    status=f"Focus room {clean_target}",
                )
        return None

    if clean_kind == FOCUS_STAGING_ROOM:
        known_rooms = {
            str(room_id) for room_id in (known_room_ids or ())
        }
        if (
            clean_target in known_rooms
            and clean_target != str(topology.heat_source_room_id or "")
            and clean_target not in set(topology.all_route_room_ids())
        ):
            return TopologyFocusEvidenceV1(
                kind=FOCUS_STAGING_ROOM,
                target_id=clean_target,
                room_id=clean_target,
                status=f"Focus staged room {clean_target}",
            )
        return None

    return None


def _project_directory(project_state: ProjectState) -> Path | None:
    value = project_state.project_dir
    if value is None:
        return None
    text = str(value).strip()
    return Path(text).resolve() if text else None


def _transaction_blocked(
    *blockers: str,
    warnings: tuple[str, ...] = (),
) -> TopologyTransactionResultV1:
    return TopologyTransactionResultV1(
        ready=False,
        blockers=tuple(_unique(blockers)),
        warnings=tuple(_unique(warnings)),
        status="Blocked — topology transaction left live ProjectState unchanged",
    )


def _restore_blocked(reason: str) -> TopologyStepbackRestoreCandidateV1:
    return TopologyStepbackRestoreCandidateV1(
        ready=False,
        blockers=(reason,),
        status="Blocked — topology step-back restore candidate unavailable",
    )


def _unique(values: Any) -> list[str]:
    out: list[str] = []
    for value in values or ():
        text = str(value or "").strip()
        if text and text not in out:
            out.append(text)
    return out
