"""Independent arithmetic, authority, persistence and stale acceptance tests."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.dev.test_hs56c_committed_point_level_balancing_reconciliation_v1 import _snapshot
from HVAC.dev.test_hs73a_pump_duty_preview_v1 import fixture as preliminary_fixture, FLUID, RHO, EnvironmentStateV1
from HVAC.hydronics.pumps.pump_preview_controller_v1 import apply_pump_preview_basis_v1
from HVAC.hydronics.pumps.pump_duty_controller_v1 import (
    apply_pump_duty_basis_v1, preview_pump_duty_v1, accept_pump_duty_v1,
    clear_pump_duty_basis_v1, clear_pump_duty_acceptance_v1,
)
from HVAC.hydronics.pumps.pump_duty_runner_v1 import valve_loss_Pa_v1
from HVAC.project.project_state import ProjectState
from HVAC.project_v3.persistence.saver import save
from HVAC.project_v3.persistence.loader import load


PRELIMINARY = dict(density_kg_m3=RHO, additional_common_loss_Pa=500,
                   head_margin_percent=10, source_note="Water basis reviewed; plant loss 500 Pa, explicit 10% reserve.")


def fixture():
    project = ProjectState(project_id="hs73b", name="Parameter-based pump duty")
    project.environment = EnvironmentStateV1()
    snapshot = _snapshot()
    section = preliminary_fixture().hydronic_proportioned_basis_snapshot.hydraulic_input_authority.sections[0]
    section = replace(section, route_ids=tuple(r.route_id for r in snapshot.hydraulic_input_authority.routes),
                      carried_flow_kg_s=0.28)
    snapshot = replace(snapshot, return_arrangement_basis="F&R",
                       hydraulic_input_authority=replace(snapshot.hydraulic_input_authority, fluid_basis=FLUID, sections=(section,)))
    project.hydronic_proportioned_basis_snapshot = snapshot
    assert apply_pump_preview_basis_v1(project, PRELIMINARY) == ()
    return project


def payload():
    return dict(
        routes=[
            dict(route_id="leg-a:route-one", pressure_Pa=100, source_note="Coil 100 Pa at committed design flow"),
            dict(route_id="leg-b:route-two", pressure_Pa=4000, source_note="Equipment 4000 Pa at committed design flow"),
            dict(route_id="leg-c:route-control", pressure_Pa=7800, source_note="Equipment/control 7800 Pa at committed design flow"),
        ],
        points=[dict(point_id="point-shared", operating_kv=3.6 * math.sqrt(1000 / RHO)),
                dict(point_id="point-route-one", operating_kv=1.8 * math.sqrt(1000 / RHO))],
        review_note="Full equipment and control basis reviewed; additional losses only; operating Kv and liquid basis reviewed.",
        reviewed=True,
    )


def apply(project, data=None):
    blockers = apply_pump_duty_basis_v1(project, payload() if data is None else data)
    assert blockers == (), blockers
    return preview_pump_duty_v1(project)


def main():
    project = fixture()
    before = deepcopy(project.to_dict())
    assert not preview_pump_duty_v1(project).ready
    assert project.to_dict() == before
    result = apply(project)
    assert result.ready and result.acceptance_ready and not result.accepted, result
    # Operating Kv scales by sqrt(1000/rho) for the new liquid basis.
    # Each point still contributes an independently constructed 4000 Pa.
    assert len(result.points) == 2
    assert all(math.isclose(p.operating_loss_Pa, 4000) for p in result.points)
    routes = {r.route_id: r for r in result.routes}
    assert math.isclose(routes['leg-a:route-one'].valve_Pa, 8000)
    assert math.isclose(routes['leg-b:route-two'].valve_Pa, 4000)
    assert routes['leg-c:route-control'].valve_Pa == 0
    assert all(math.isclose(r.total_Pa, 9100) for r in result.routes)
    assert all(abs(r.residual_Pa) < 1e-9 for r in result.routes)
    # Old balancing allocations 300/200/0 are NOT added to these totals.
    assert math.isclose(result.numbers.pressure_Pa, (9100+500)*1.1)
    assert math.isclose(result.numbers.flow_m3_h, 1008 / RHO)
    assert math.isclose(result.numbers.head_m, 10560/(RHO*9.81))
    assert len(result.controlling_route_ids) == 3
    snapshot = project.hydronic_proportioned_basis_snapshot
    assert preview_pump_duty_v1(project) == result
    assert accept_pump_duty_v1(project, "wrong-screen-fingerprint")
    assert project.hydronic_pump_duty_acceptance is None
    assert accept_pump_duty_v1(project, result.basis_fingerprint) == ()
    assert preview_pump_duty_v1(project).accepted
    assert project.hydronic_proportioned_basis_snapshot is snapshot
    changed = {k for k,v in project.to_dict().items() if v != before.get(k)}
    assert changed == {"hydronic_pump_duty_basis", "hydronic_pump_duty_acceptance"}, changed
    with TemporaryDirectory() as temporary:
        save(project, Path(temporary))
        restored = load(Path(temporary))
        assert preview_pump_duty_v1(restored).accepted
        assert preview_pump_duty_v1(restored).basis_fingerprint == result.basis_fingerprint
    old = deepcopy(project.to_dict())
    old.pop("hydronic_pump_duty_basis");old.pop("hydronic_pump_duty_acceptance")
    legacy = ProjectState.from_dict(old)
    assert legacy.hydronic_pump_duty_basis is None and legacy.hydronic_pump_duty_acceptance is None

    # Malformed persisted shape never becomes accepted intent or crashes review.
    for field, value in [('reviewed', 'false'), ('review_note', {}), ('routes', None)]:
        bad = deepcopy(project.to_dict())
        bad['hydronic_pump_duty_basis'][field] = value
        assert not preview_pump_duty_v1(ProjectState.from_dict(bad)).accepted
    data = payload(); data['routes'][0]['route_id'] = []
    assert apply_pump_duty_basis_v1(project, data)
    bad = deepcopy(project.to_dict())
    bad['hydronic_pump_duty_basis']['routes'][0]['route_id'] = []
    assert not preview_pump_duty_v1(ProjectState.from_dict(bad)).accepted

    # No hidden repair; invalid input leaves the accepted basis and duty intact.
    for bad in (True, -1, "", None, "nan", "inf", -float('inf')):
        data=payload();data['routes'][0]['pressure_Pa']=bad
        saved=deepcopy(project.to_dict())
        assert apply_pump_duty_basis_v1(project,data)
        assert project.to_dict()==saved
    for bad in (True, 0, -1, "nan", "inf", 100):
        data=payload();data['points'][0]['operating_kv']=bad
        assert apply_pump_duty_basis_v1(project,data)
    for kind in ('missing-route','duplicate-route','unknown-route','missing-point','duplicate-point','empty-note','review-string','overflow'):
        data=payload()
        if kind=='missing-route':data['routes'].pop()
        if kind=='duplicate-route':data['routes'].append(data['routes'][0])
        if kind=='unknown-route':data['routes'][0]['route_id']='other'
        if kind=='missing-point':data['points'].pop()
        if kind=='duplicate-point':data['points'].append(data['points'][0])
        if kind=='empty-note':data['routes'][0]['source_note']=' '
        if kind=='review-string':data['reviewed']='false'
        if kind=='overflow':data['points'][0]['operating_kv']=1e-300
        assert apply_pump_duty_basis_v1(project,data),kind
        assert preview_pump_duty_v1(project).accepted
    # Explicit zero equipment losses are supported, but do not assert balance.
    data=payload();data['routes'][0]['pressure_Pa']=0
    result=apply(project,data)
    assert result.ready and not result.acceptance_ready and not result.accepted
    assert any('reconcile' in b for b in result.acceptance_blockers)
    data=payload();data['points'][0]['operating_kv']=''
    result=apply(project,data)
    assert result.ready and not result.acceptance_ready
    assert any('Kvs alone' in b for b in result.acceptance_blockers)
    assert accept_pump_duty_v1(project,result.basis_fingerprint)
    data=payload();data['reviewed']=False
    result=apply(project,data)
    assert not result.acceptance_ready and any('Confirm' in b for b in result.acceptance_blockers)
    # Equipment may change the controlling route; recompute from final totals.
    data=payload();data['routes'][1]['pressure_Pa']=6000
    result=apply(project,data)
    assert result.controlling_route_ids == ('leg-b:route-two',)
    assert math.isclose(result.numbers.pressure_Pa,(11100+500)*1.1)
    result=apply(project)
    assert accept_pump_duty_v1(project,result.basis_fingerprint)==()
    # Tampered numeric acceptance never resolves as accepted.
    accepted=project.hydronic_pump_duty_acceptance
    project.hydronic_pump_duty_acceptance=replace(accepted,pressure_Pa=1)
    assert not preview_pump_duty_v1(project).accepted
    project.hydronic_pump_duty_acceptance=accepted
    for field,value in [('density_kg_m3',998),('additional_common_loss_Pa',600),('head_margin_percent',20)]:
        original=project.hydronic_pump_preview_basis
        project.hydronic_pump_preview_basis=replace(original,**{field:value})
        assert not preview_pump_duty_v1(project).ready
        assert accept_pump_duty_v1(project,result.basis_fingerprint)
        project.hydronic_pump_preview_basis=original
    # Live unrelated engineering edits do not alter this committed-basis review.
    project.name='Unrelated live edit'
    assert preview_pump_duty_v1(project).accepted
    project.hydronic_proportioned_basis_snapshot=replace(snapshot,note='Changed committed evidence')
    assert not preview_pump_duty_v1(project).ready
    project.hydronic_proportioned_basis_snapshot=snapshot
    # Reject inconsistent point-route membership even if stored conserved=True.
    authority=snapshot.point_allocation_authority
    broken=replace(authority.rows[0],downstream_route_ids=('route-one',))
    project.hydronic_proportioned_basis_snapshot=replace(snapshot,point_allocation_authority=replace(authority,rows=(broken,*authority.rows[1:])))
    assert apply_pump_preview_basis_v1(project,PRELIMINARY)==()
    assert not preview_pump_duty_v1(project).ready
    assert apply_pump_duty_basis_v1(project,payload())
    project.hydronic_proportioned_basis_snapshot=snapshot
    assert apply_pump_preview_basis_v1(project,PRELIMINARY)==()
    clear_pump_duty_acceptance_v1(project)
    assert project.hydronic_pump_duty_acceptance is None
    assert project.hydronic_pump_duty_basis is not None
    clear_pump_duty_basis_v1(project)
    assert project.hydronic_pump_duty_basis is None
    # Independent non-water check: at fixed mass flow, dp varies inversely with density.
    assert math.isclose(valve_loss_Pa_v1(mass_flow_kg_s=.2,density_kg_m3=800,kv=3.6),5000)
    assert math.isclose(valve_loss_Pa_v1(mass_flow_kg_s=.2,density_kg_m3=1000,kv=3.6),4000)
    print('OK — H-S73-B route/Kv ledger, no double counting, changed controlling route, explicit acceptance, stale rejection and checksummed save/load.')


if __name__=='__main__':main()
