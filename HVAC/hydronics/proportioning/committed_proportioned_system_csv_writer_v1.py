# ======================================================================
# H-S60-A — Deterministic committed Proportioned-system CSV bundle writer
# ======================================================================

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
from io import StringIO
import json
from pathlib import Path
import shutil
import tempfile

from HVAC.hydronics.proportioning.committed_proportioned_system_export_payload_v1 import (
    CommittedProportionedSystemExportPayloadV1,
)


SUMMARY_FILE_V1 = "proportioned_summary.csv"
ROUTES_FILE_V1 = "proportioned_routes.csv"
BALANCING_POINTS_FILE_V1 = "proportioned_balancing_points.csv"
ROUTE_POINT_FILE_V1 = "proportioned_route_point_reconciliation.csv"
SECTIONS_FILE_V1 = "proportioned_sections.csv"

CSV_BUNDLE_FILE_NAMES_V1: tuple[str, ...] = (
    SUMMARY_FILE_V1,
    ROUTES_FILE_V1,
    BALANCING_POINTS_FILE_V1,
    ROUTE_POINT_FILE_V1,
    SECTIONS_FILE_V1,
)


@dataclass(frozen=True, slots=True)
class CommittedProportionedCsvFileV1:
    file_name: str
    row_count: int
    sha256: str


@dataclass(frozen=True, slots=True)
class CommittedProportionedCsvBundleWriteResultV1:
    schema: str = "committed_proportioned_csv_bundle_write_result_v1"
    ready: bool = False
    destination_directory: str = ""
    files: tuple[CommittedProportionedCsvFileV1, ...] = ()
    status: str = "Committed Proportioned CSV bundle not written"
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No ProjectState mutation or additional persistence",
        "No live preview evidence used",
        "No hydraulic, friction or pressure calculation",
        "No PDF report written",
        "No GUI export control",
        "No pump selection",
        "No valve product or valve setting selected",
        "No pipe resizing",
        "No commissioning or final system balancing",
    )
    note: str = (
        "Five UTF-8 CSV files written from one ready committed H-S59-B "
        "payload; existing destinations are never overwritten."
    )


def write_committed_proportioned_csv_bundle_v1(
    payload: CommittedProportionedSystemExportPayloadV1 | None,
    destination_directory: str | Path,
) -> CommittedProportionedCsvBundleWriteResultV1:
    """
    Atomically publish five deterministic CSV files.

    All files are rendered before disk mutation. They are then written to a
    private temporary directory and the directory is renamed into place only
    after every write and checksum succeeds.
    """
    destination_text = str(destination_directory or "").strip()
    if not destination_text:
        return _blocked_v1("Destination directory required")
    destination = Path(destination_text)

    if not isinstance(
        payload,
        CommittedProportionedSystemExportPayloadV1,
    ):
        return _blocked_v1(
            "H-S59-B committed export/report payload required",
            destination=destination,
        )
    if not payload.ready:
        upstream = tuple(
            f"H-S59-B: {value}"
            for value in tuple(payload.blockers or ())
            if _text_v1(value)
        )
        return _blocked_v1(
            *(
                upstream
                or (
                    "H-S59-B: "
                    + (
                        _text_v1(payload.status)
                        or "committed export payload is not ready"
                    ),
                )
            ),
            destination=destination,
        )
    if destination.exists():
        return _blocked_v1(
            "Destination already exists; committed CSV export will not "
            "overwrite it",
            destination=destination,
        )
    parent = destination.parent
    if not parent.is_dir():
        return _blocked_v1(
            "Destination parent directory must already exist",
            destination=destination,
        )

    try:
        rendered = _render_csv_bundle_v1(payload)
    except (TypeError, ValueError) as exc:
        return _blocked_v1(
            f"Committed CSV payload is incomplete: {exc}",
            destination=destination,
        )

    temporary: Path | None = None
    try:
        temporary = Path(
            tempfile.mkdtemp(
                prefix=f".{destination.name}.",
                dir=str(parent),
            )
        )
        file_results: list[CommittedProportionedCsvFileV1] = []
        for file_name, text, row_count in rendered:
            target = temporary / file_name
            with target.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as stream:
                stream.write(text)
            data = target.read_bytes()
            expected = text.encode("utf-8")
            if data != expected:
                raise OSError(
                    f"Written CSV bytes differ from rendered content: "
                    f"{file_name}"
                )
            file_results.append(
                CommittedProportionedCsvFileV1(
                    file_name=file_name,
                    row_count=row_count,
                    sha256=hashlib.sha256(data).hexdigest(),
                )
            )

        if destination.exists():
            raise FileExistsError(
                "Destination appeared during CSV export; refusing overwrite"
            )
        temporary.replace(destination)
        temporary = None
        return CommittedProportionedCsvBundleWriteResultV1(
            ready=True,
            destination_directory=str(destination),
            files=tuple(file_results),
            status=(
                "Ready — deterministic committed Proportioned CSV bundle "
                "written"
            ),
        )
    except OSError as exc:
        return _blocked_v1(
            f"Committed CSV bundle write failed: {exc}",
            destination=destination,
        )
    finally:
        if temporary is not None and temporary.exists():
            shutil.rmtree(temporary)


def _render_csv_bundle_v1(
    payload: CommittedProportionedSystemExportPayloadV1,
) -> tuple[tuple[str, str, int], ...]:
    if not isinstance(payload.summary, dict) or not payload.summary:
        raise ValueError("committed summary rows required")

    route_rows = tuple(payload.committed_route_results or ())
    point_rows = tuple(payload.committed_balancing_point_results or ())
    route_point_rows = tuple(
        payload.committed_route_point_reconciliation or ()
    )
    section_rows = tuple(payload.committed_section_results or ())
    for label, rows in (
        ("route", route_rows),
        ("balancing-point", point_rows),
        ("route/point reconciliation", route_point_rows),
        ("section", section_rows),
    ):
        if not rows:
            raise ValueError(f"committed {label} rows required")

    summary_rows: list[dict[str, object]] = [
        {"item": "export_payload_schema", "value": payload.schema},
        {"item": "export_payload_status", "value": payload.status},
        {
            "item": "source_package_schema",
            "value": payload.source_package_schema,
        },
        {
            "item": "accepted_return_arrangement_basis",
            "value": payload.accepted_return_arrangement_basis,
        },
    ]
    summary_rows.extend(
        {"item": str(key), "value": value}
        for key, value in payload.summary.items()
    )
    summary_rows.extend(
        (
            {"item": "exclusions", "value": tuple(payload.exclusions)},
            {"item": "note", "value": payload.note},
        )
    )

    return (
        (
            SUMMARY_FILE_V1,
            _render_rows_v1(summary_rows, ("item", "value")),
            len(summary_rows),
        ),
        (
            ROUTES_FILE_V1,
            _render_rows_v1(route_rows),
            len(route_rows),
        ),
        (
            BALANCING_POINTS_FILE_V1,
            _render_rows_v1(point_rows),
            len(point_rows),
        ),
        (
            ROUTE_POINT_FILE_V1,
            _render_rows_v1(route_point_rows),
            len(route_point_rows),
        ),
        (
            SECTIONS_FILE_V1,
            _render_rows_v1(section_rows),
            len(section_rows),
        ),
    )


def _render_rows_v1(
    rows,
    field_names: tuple[str, ...] | None = None,
) -> str:
    clean_rows = tuple(dict(row or {}) for row in tuple(rows or ()))
    if not clean_rows:
        raise ValueError("at least one CSV row required")
    fields = field_names or _ordered_fields_v1(clean_rows)
    if not fields:
        raise ValueError("at least one CSV field required")

    stream = StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(fields),
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in clean_rows:
        writer.writerow(
            {
                field: _csv_cell_v1(row.get(field))
                for field in fields
            }
        )
    return stream.getvalue()


def _ordered_fields_v1(rows) -> tuple[str, ...]:
    fields: list[str] = []
    for row in rows:
        for key in row:
            name = str(key)
            if name not in fields:
                fields.append(name)
    return tuple(fields)


def _csv_cell_v1(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return value
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    return str(value)


def _blocked_v1(
    *blockers: str,
    destination: Path | None = None,
) -> CommittedProportionedCsvBundleWriteResultV1:
    clean = _unique_v1(blockers)
    return CommittedProportionedCsvBundleWriteResultV1(
        ready=False,
        destination_directory=(
            str(destination) if destination is not None else ""
        ),
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _unique_v1(values) -> tuple[str, ...]:
    output: list[str] = []
    for value in values:
        text = _text_v1(value)
        if text and text not in output:
            output.append(text)
    return tuple(output)
