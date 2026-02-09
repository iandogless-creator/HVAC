# HVAC/project_v3/run/hydronics_sanity_engine.py

def hydronics_qt_sanity(project) -> float:
    ps = project.project_state
    qt = hydronics_qt_sanity(project)
    print(f"[HydronicsSanity] Qt received = {qt:.2f} W")

    topo = project.hydronic_topology
    print("[Hydronics] legs:", list(topo.legs.keys()))
    print("[Hydronics] roots:", topo.boiler_leg_ids)

    if not ps.heatloss_valid:
        raise RuntimeError("Heat-loss not authoritative")

    if ps.heatloss_qt_w is None:
        raise RuntimeError("Qt missing")

    # Just echo for now
    return ps.heatloss_qt_w

def fake_index_leg(topology):
    return max(
        topology.legs.values(),
        key=lambda leg: leg.design_heat_w or 0.0
    )
    leg = fake_index_leg(topo)
    print(f"[Hydronics] Index leg (FAKE): {leg.leg_id}")
