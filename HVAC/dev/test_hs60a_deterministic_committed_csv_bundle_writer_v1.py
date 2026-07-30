# ======================================================================
# H-S60-A — Deterministic committed CSV bundle writer test
# ======================================================================

from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.hydronics.proportioning.committed_proportioned_system_csv_writer_v1 import (
    CSV_BUNDLE_FILE_NAMES_V1,
    write_committed_proportioned_csv_bundle_v1,
)
from HVAC.hydronics.proportioning.committed_proportioned_system_export_payload_v1 import (
    CommittedProportionedSystemExportPayloadV1,
)


def _payload():
    return CommittedProportionedSystemExportPayloadV1(
        ready=True,
        status="Ready",
        source_package_schema=(
            "committed_proportioned_system_result_package_v1"
        ),
        accepted_return_arrangement_basis="DIRECT_RETURN",
        summary={
            "route_count": 1,
            "balancing_point_count": 1,
            "unique_section_count": 1,
            "valve_duty_point_count": 1,
        },
        committed_route_results=(
            {
                "route_id": "route-a",
                "route_label": "Route A",
                "proportioned_pressure_drop_Pa": 40_000.0,
                "ready": True,
                "blockers": (),
            },
        ),
        committed_balancing_point_results=(
            {
                "balancing_point_id": "point-a",
                "allocated_added_pressure_drop_Pa": 1_000.0,
                "accepted_kvs_basis": 6.3,
                "reconciled": True,
            },
        ),
        committed_route_point_reconciliation=(
            {
                "committed_route_id": "route-a",
                "contributing_balancing_point_ids": ("point-a",),
                "reconciled": True,
            },
        ),
        committed_section_results=(
            {
                "committed_route_id": "route-a",
                "section_id": "section-a",
                "pipe_size_label": "15 mm",
                "carried_flow_kg_s": 0.1,
            },
        ),
    )


def _bytes_by_name(directory: Path) -> dict[str, bytes]:
    return {
        name: (directory / name).read_bytes()
        for name in CSV_BUNDLE_FILE_NAMES_V1
    }


def main() -> None:
    payload = _payload()
    before = repr(payload)

    with TemporaryDirectory() as temporary_text:
        temporary = Path(temporary_text)
        first_directory = temporary / "committed-csv-a"
        result = write_committed_proportioned_csv_bundle_v1(
            payload,
            first_directory,
        )

        assert result.ready is True, result.status
        assert result.blockers == ()
        assert Path(result.destination_directory) == first_directory
        assert tuple(row.file_name for row in result.files) == (
            CSV_BUNDLE_FILE_NAMES_V1
        )
        assert tuple(row.row_count for row in result.files) == (
            10,
            1,
            1,
            1,
            1,
        )
        assert all(len(row.sha256) == 64 for row in result.files)
        assert set(path.name for path in first_directory.iterdir()) == (
            set(CSV_BUNDLE_FILE_NAMES_V1)
        )
        assert all(
            b"\r\n" not in data
            for data in _bytes_by_name(first_directory).values()
        )

        with (
            first_directory / "proportioned_routes.csv"
        ).open(encoding="utf-8", newline="") as stream:
            route_rows = list(csv.DictReader(stream))
        assert route_rows[0]["route_id"] == "route-a"
        assert route_rows[0]["ready"] == "true"
        assert route_rows[0]["blockers"] == "[]"

        with (
            first_directory / "proportioned_summary.csv"
        ).open(encoding="utf-8", newline="") as stream:
            summary_rows = {
                row["item"]: row["value"]
                for row in csv.DictReader(stream)
            }
        assert summary_rows["route_count"] == "1"
        assert (
            summary_rows["accepted_return_arrangement_basis"]
            == "DIRECT_RETURN"
        )

        second_directory = temporary / "committed-csv-b"
        second = write_committed_proportioned_csv_bundle_v1(
            payload,
            second_directory,
        )
        assert second.ready is True
        assert _bytes_by_name(first_directory) == _bytes_by_name(
            second_directory
        )
        assert tuple(row.sha256 for row in result.files) == tuple(
            row.sha256 for row in second.files
        )

        existing_directory = temporary / "existing"
        existing_directory.mkdir()
        sentinel = existing_directory / "keep.txt"
        sentinel.write_text("preserve", encoding="utf-8")
        existing = write_committed_proportioned_csv_bundle_v1(
            payload,
            existing_directory,
        )
        assert existing.ready is False
        assert "will not overwrite" in existing.status
        assert sentinel.read_text(encoding="utf-8") == "preserve"

        blocked_directory = temporary / "blocked"
        blocked = write_committed_proportioned_csv_bundle_v1(
            replace(
                payload,
                ready=False,
                status="Blocked",
                blockers=("payload incomplete",),
            ),
            blocked_directory,
        )
        assert blocked.ready is False
        assert "H-S59-B: payload incomplete" in blocked.blockers
        assert not blocked_directory.exists()

        incomplete_directory = temporary / "incomplete"
        incomplete = write_committed_proportioned_csv_bundle_v1(
            replace(payload, committed_section_results=()),
            incomplete_directory,
        )
        assert incomplete.ready is False
        assert "committed section rows required" in incomplete.status
        assert not incomplete_directory.exists()

    assert repr(payload) == before
    assert "No PDF report written" in result.exclusions
    assert "No GUI export control" in result.exclusions

    print(
        "OK — H-S60-A deterministic committed CSV bundle writer passed."
    )


if __name__ == "__main__":
    main()
