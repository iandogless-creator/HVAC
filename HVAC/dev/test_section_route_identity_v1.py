from HVAC.hydronics.proportioning.section_route_identity_v1 import (
    enrich_basic_ps_section_rows_with_route_identity_v1,
    infer_section_route_identity_v1,
)


def main() -> None:
    row = {
        "section_id": "leg-001-primary-subleg-section-001",
        "from": "Common main / leg entry",
        "to": "L1A-R01",
        "flow_kg_s": "0.0467 kg/s",
    }

    identity = infer_section_route_identity_v1(row)

    print("ROUTE CODE:", identity.route_code)
    print("LEG ID:", identity.leg_id)
    print("SUBLEG ID:", identity.subleg_id)
    print("ROUTE ID:", identity.route_id)
    print("ROLE:", identity.subleg_role)
    print("TAKEOFF:", identity.takeoff_status)

    enriched = enrich_basic_ps_section_rows_with_route_identity_v1([row])[0]
    print("ENRICHED:", enriched)

    assert identity.route_code == "L1A"
    assert identity.leg_id == "leg-001"
    assert identity.subleg_id == "leg-001-primary-subleg"
    assert identity.route_id == "leg-001-primary-subleg"
    assert identity.subleg_role == "common"


if __name__ == "__main__":
    main()