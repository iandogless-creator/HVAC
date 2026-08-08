from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.project.project_state import ProjectState
from HVAC.project_v3.persistence.loader import load
from HVAC.project_v3.persistence.saver import MAX_BACKUPS, save


def _expect_load_error(path: Path, expected_text: str) -> None:
    try:
        load(path)
    except ValueError as exc:
        assert expected_text in str(exc), str(exc)
    else:
        raise AssertionError(f"Expected load failure containing {expected_text!r}")


def main() -> None:
    assert MAX_BACKUPS == 20

    with TemporaryDirectory(prefix="hs67a2-") as temporary_directory:
        project_dir = Path(temporary_directory)
        project = ProjectState(project_id="hs67a2", name="save-00")

        for index in range(25):
            project.name = f"save-{index:02d}"
            save(project, project_dir)

        assert load(project_dir).name == "save-24"

        backup_paths = [
            project_dir / f"project.backup.{index}.json"
            for index in range(1, MAX_BACKUPS + 1)
        ]
        assert all(path.is_file() for path in backup_paths)
        assert not (project_dir / "project.backup.21.json").exists()

        for backup_index, backup_path in enumerate(backup_paths, start=1):
            expected_save_index = 24 - backup_index
            assert load(backup_path).name == f"save-{expected_save_index:02d}"

        project_file = project_dir / "project.json"
        wrapped = json.loads(project_file.read_text(encoding="utf-8"))

        tampered = dict(wrapped)
        tampered["payload"] = dict(wrapped["payload"])
        tampered["payload"]["name"] = "tampered without checksum update"
        tampered_path = project_dir / "tampered.json"
        tampered_path.write_text(
            json.dumps(tampered, indent=2, sort_keys=True), encoding="utf-8"
        )
        _expect_load_error(tampered_path, "checksum mismatch")

        unsupported = dict(wrapped)
        unsupported["schema_version"] = 999
        unsupported_path = project_dir / "unsupported.json"
        unsupported_path.write_text(
            json.dumps(unsupported, indent=2, sort_keys=True), encoding="utf-8"
        )
        _expect_load_error(unsupported_path, "wrapper schema version")

        incomplete = dict(wrapped)
        incomplete.pop("checksum")
        incomplete_path = project_dir / "incomplete.json"
        incomplete_path.write_text(
            json.dumps(incomplete, indent=2, sort_keys=True), encoding="utf-8"
        )
        _expect_load_error(incomplete_path, "wrapper structure")

        legacy_path = project_dir / "legacy-unwrapped.json"
        legacy_path.write_text(
            json.dumps(project.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        assert load(legacy_path).name == "save-24"

    print(
        "OK — H-S67-A2 validates modern project wrappers, preserves "
        "legacy unwrapped payloads and retains 20 ordered save backups."
    )


if __name__ == "__main__":
    main()
