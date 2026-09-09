# ======================================================================
# H-S70-B2E — clear-only orphan Kvs intent rows
# ======================================================================

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)


def ns(**values):
    return SimpleNamespace(**values)


def main() -> None:
    current = "balancing-point:leg:current"
    orphan_acceptance = "balancing-point:main:leg-002"
    orphan_disposition = (
        "balancing-point:subleg:leg-001-primary-subleg:"
        "downstream-exclusive"
    )
    dormant = "balancing-point:main:dormant"

    utilisation = ns(
        rows=(
            ns(balancing_point_id=current, kvs_candidates=(1.6, 2.5)),
            ns(balancing_point_id=orphan_acceptance, kvs_candidates=()),
            ns(balancing_point_id=orphan_disposition, kvs_candidates=()),
            ns(balancing_point_id=dormant, kvs_candidates=()),
        )
    )
    acceptance = ns(
        rows=(
            ns(
                balancing_point_id=current,
                accepted_kvs=None,
                accepted=False,
                status="Manual Kvs candidate acceptance pending",
                blockers=(),
            ),
            ns(
                balancing_point_id=orphan_acceptance,
                accepted_kvs=2.5,
                accepted=False,
                status="Blocked — obsolete acceptance",
                blockers=("No current candidate is required",),
            ),
        )
    )
    consequence = ns(rows=())
    disposition = ns(
        rows=(
            ns(
                balancing_point_id=orphan_disposition,
                disposition="approved_for_product_search",
                status="Blocked — obsolete disposition",
                blockers=("No current consequence is required",),
            ),
        )
    )
    display_rows = [
        {
            "balancing_point_id": point_id,
            "point_scope": "point",
            "point_role": "test",
            "required_kv": "—",
            "kvs_candidates": "—",
            "kvs_utilisation": "—",
        }
        for point_id in (
            current,
            orphan_acceptance,
            orphan_disposition,
            dormant,
        )
    ]

    rows = (
        HydronicsSchematicPanelAdapter.
        _build_balancing_point_kvs_acceptance_editor_rows_v1(
            point_display_rows=display_rows,
            utilisation_evidence=utilisation,
            acceptance_resolution=acceptance,
            consequence_evidence=consequence,
            disposition_resolution=disposition,
        )
    )
    by_id = {row["balancing_point_id"]: row for row in rows}

    assert set(by_id) == {
        current,
        orphan_acceptance,
        orphan_disposition,
    }
    assert dormant not in by_id
    assert by_id[orphan_acceptance]["kvs_candidates"] == ()
    assert by_id[orphan_acceptance]["accepted_kvs"] == 2.5
    assert by_id[orphan_disposition]["kvs_candidates"] == ()
    assert (
        by_id[orphan_disposition]["consequence_disposition"]
        == "approved_for_product_search"
    )

    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    assert "candidate_combo.setEnabled(bool(candidates))" in panel_source
    assert "accepted_kvs is not None" in panel_source
    assert "bool(disposition_value)" in panel_source

    print(
        "OK — H-S70-B2E exposes only stored orphan point Kvs decisions as "
        "clear-only editor rows, keeps dormant no-valve points hidden and "
        "does not weaken current-candidate acceptance authority."
    )


if __name__ == "__main__":
    main()
