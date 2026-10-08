"""H-S73-C: published values, live consumers, frozen authority and stale gates."""
from copy import deepcopy
from dataclasses import replace
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from HVAC.fluid.water_properties_v1 import *
from HVAC.dev.test_hs40b_common_main_leg_entry_pipe_sizing_v1 import _project
from HVAC.dev.test_hs42c_route_specific_main_pressure_accumulation_v1 import _install_lengths
from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import build_route_pressure_accumulator_v1
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    build_committed_proportioning_hydraulic_input_authority_v1,
    committed_proportioning_hydraulic_input_authority_to_dict_v1,
    committed_proportioning_hydraulic_input_authority_from_dict_v1)
from HVAC.hydronics.proportioning import proportioned_basis_snapshot_v1 as snapshots
from HVAC.hydronics.proportioning.proportioned_pipe_sizing_authority_v1 import (
    build_proportioned_pipe_sizing_authority_v1, ProportionedPipeSizingCriteriaV1)
from HVAC.hydronics.proportioning.proportioned_pipe_size_candidate_evaluation_v1 import build_proportioned_pipe_size_candidate_evaluation_v1
from HVAC.hydronics.proportioning.proportioned_pipe_resizing_hydraulic_projection_v1 import build_proportioned_pipe_resizing_hydraulic_projection_v1
from HVAC.hydronics.proportioning.balancing_point_required_kv_preview_v1 import calculate_required_kv_v1
from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_hydraulic_consequence_v1 import calculate_accepted_kvs_hydraulic_consequence_v1
from HVAC.hydronics.pumps.pump_duty_runner_v1 import valve_loss_Pa_v1
from HVAC.hydronics.pumps.pump_preview_controller_v1 import preview_pump_v1, apply_pump_preview_basis_v1, pump_preview_draft_defaults_v1
from HVAC.hydronics.pumps.pump_duty_controller_v1 import preview_pump_duty_v1, accept_pump_duty_v1
from HVAC.project.project_state import ProjectState
from HVAC.project_v3.persistence.saver import save
from HVAC.project_v3.persistence.loader import load


def live_authority(project):
    projection = build_route_pressure_accumulator_v1(project)
    target = max(r.route_pressure_drop_total_Pa for r in projection.rows)
    chosen = tuple(NS(route_id=r.route_id, route=r.route_label, basis='F&R',
        chosen_dp_pa=r.route_pressure_drop_total_Pa, is_controlling=r.route_pressure_drop_total_Pa==target) for r in projection.rows)
    resistance = NS(rows=tuple(NS(route_id=r.route_id, required_added_dp=target-r.chosen_dp_pa,
        resistance_pa_per_kg_s2=0) for r in chosen))
    authority = build_committed_proportioning_hydraulic_input_authority_v1(
        route_pressure_projection=projection, chosen_controlling_rows=chosen, resistance_basis=resistance)
    assert authority.ready, authority.blockers
    return projection, authority


class SharedWaterTests(unittest.TestCase):
    def close(self,a,b): self.assertTrue(math.isclose(a,b,rel_tol=1e-11),(a,b))

    def test_iapws_table8_and_validation(self):
        # Published Table 8, independent of this implementation.
        for t,rho,micro in [(260,997.068360,3058.36075),(298.15,997.047013,889.996774),(375,957.009710,276.207245)]:
            r,m=water_properties_at_temperature_v1(t-273.15)
            self.assertTrue(math.isclose(r,rho,rel_tol=1e-9))
            self.assertTrue(math.isclose(m*1e6,micro,rel_tol=2e-9))
        for t in (-20.01,110.01,float('nan'),float('inf'),None,True,'70'):
            with self.assertRaises(ValueError):water_properties_at_temperature_v1(t)
        for flow,ret in ((None,65),(75,None),(65,75),(65,65),(96,65),(75,4),(True,5)):
            with self.assertRaises(ValueError):build_water_hydraulic_basis_v1(flow,ret)
        with self.assertRaises(ValueError):resolve_project_water_basis_v1(NS())
        fluid=build_water_hydraulic_basis_v1(75,65);self.assertEqual(fluid.temperature_c,70)
        for key,value in [('model_id','other'),('density_kg_m3',998),('dynamic_viscosity_Pa_s',.001),
            ('fluid_key','PG_30'),('reference_pressure_Pa',300000),('temperature_c',True)]:
            raw=fluid.to_dict();raw[key]=value
            with self.assertRaises(ValueError):water_hydraulic_basis_from_dict_v1(raw)

    def test_pipe_local_k_return_and_resize_consistency(self):
        from HVAC.hydronics.proportioning.circuit_return_path_comparison_v1 import _rr_added_length_pressure_drop_Pa, _RRSectionPressureBasisV1
        project=_project();_install_lengths(project);before=deepcopy(project.to_dict())
        projection,authority=live_authority(project);fluid=resolve_project_water_basis_v1(project)
        self.assertEqual(authority.fluid_basis,fluid);self.assertEqual(project.to_dict(),before)
        for s in authority.sections:
            d=s.internal_diameter_m;rho=fluid.density_kg_m3;mu=fluid.dynamic_viscosity_Pa_s
            v=s.carried_flow_kg_s/rho/(math.pi*d*d/4)
            self.close(s.velocity_m_s,v);self.close(s.reynolds_number,rho*v*d/mu)
            self.close(s.local_pressure_drop_Pa,s.k_total*rho*v*v/2)
            self.close(s.straight_pressure_drop_Pa,s.friction_factor*s.length_m/d*rho*v*v/2)
        s=authority.sections[0]
        rr=_rr_added_length_pressure_drop_Pa(project_state=project,
            section_pressure_basis_by_id={'s':_RRSectionPressureBasisV1(mass_flow_kg_s=s.carried_flow_kg_s,
            material_key=s.material_key,pipe_size_key=s.dn,pipe_size_label=s.pipe_size_label)},candidate_section_ids=('s',),length_m=s.length_m)
        self.close(rr,s.straight_pressure_drop_Pa)
        project.hydronic_proportioned_basis_snapshot=snapshots.ProportionedBasisSnapshotV1(return_arrangement_basis='F&R',hydraulic_input_authority=authority)
        criteria=ProportionedPipeSizingCriteriaV1(density_kg_m3=fluid.density_kg_m3,
            dynamic_viscosity_Pa_s=fluid.dynamic_viscosity_Pa_s,require_fluid_basis=True)
        sizing=build_proportioned_pipe_sizing_authority_v1(project.hydronic_proportioned_basis_snapshot,criteria=criteria)
        self.assertTrue(sizing.ready,sizing.blockers)
        result=build_proportioned_pipe_resizing_hydraulic_projection_v1(authority=sizing,
            candidate_evaluation=build_proportioned_pipe_size_candidate_evaluation_v1(sizing))
        self.assertTrue(result.ready,result.blockers);self.assertEqual(result.fluid_basis,fluid)
        for s in result.sections:self.close(s.reynolds_number,fluid.density_kg_m3*s.velocity_m_s*s.internal_diameter_m/fluid.dynamic_viscosity_Pa_s)
        bad=build_proportioned_pipe_sizing_authority_v1(project.hydronic_proportioned_basis_snapshot,criteria=replace(criteria,dynamic_viscosity_Pa_s=.001))
        self.assertFalse(bad.ready)
        project.environment.design_flow_temp_c=45;project.environment.design_return_temp_c=35
        cooler,_=live_authority(project);self.assertNotEqual(cooler.rows,projection.rows)
        self.assertEqual(project.hydronic_proportioned_basis_snapshot.hydraulic_input_authority,authority)

    def test_kv_inverse_consistency(self):
        for mean in (20,40,70,90):
            rho,_=water_properties_at_temperature_v1(mean)
            q,_,kv=calculate_required_kv_v1(mass_flow_kg_s=.2,design_valve_dp_pa=4000,fluid_density_kg_m3=rho)
            self.close(kv,(.2*3600/rho)*math.sqrt((rho/1000)/.04))
            self.close(valve_loss_Pa_v1(mass_flow_kg_s=.2,density_kg_m3=rho,kv=kv),4000)
            _,dp,_=calculate_accepted_kvs_hydraulic_consequence_v1(flow_m3_h=q,accepted_kvs=kv,controlled_circuit_dp_pa=12000,fluid_density_kg_m3=rho)
            self.close(dp,4000)

    def test_legacy_and_corrupt_evidence(self):
        from HVAC.dev.test_hs73a_pump_duty_preview_v1 import fixture
        project=fixture();snapshot=project.hydronic_proportioned_basis_snapshot
        project.hydronic_proportioned_basis_snapshot=replace(snapshot,hydraulic_input_authority=replace(snapshot.hydraulic_input_authority,fluid_basis=None))
        before=deepcopy(project.to_dict());restored=ProjectState.from_dict(before)
        self.assertIsNotNone(restored.hydronic_proportioned_basis_snapshot)
        self.assertNotIn('fluid_basis',before['hydronic_proportioned_basis_snapshot']['hydraulic_input_authority'])
        self.assertTrue(any('Legacy' in b for b in preview_pump_v1(restored).blockers))
        normalised=deepcopy(restored.to_dict())
        self.assertNotIn('density_kg_m3',pump_preview_draft_defaults_v1(restored))
        self.assertEqual(normalised,restored.to_dict())
        raw=committed_proportioning_hydraulic_input_authority_to_dict_v1(snapshot.hydraulic_input_authority)
        raw['fluid_basis']['density_kg_m3']=998
        self.assertIsNone(committed_proportioning_hydraulic_input_authority_from_dict_v1(raw))

    def test_stale_duty_and_checksummed_persistence(self):
        from HVAC.dev.test_hs73b_pump_duty_v1 import fixture,apply
        project=fixture();result=apply(project)
        self.assertEqual(accept_pump_duty_v1(project,result.basis_fingerprint),())
        snapshot=project.hydronic_proportioned_basis_snapshot;acceptance=project.hydronic_pump_duty_acceptance
        with TemporaryDirectory() as directory:
            save(project,Path(directory));restored=load(Path(directory))
        self.assertTrue(preview_pump_duty_v1(restored).accepted)
        for flow,ret in ((65,55),(80,60)):
            project.environment.design_flow_temp_c=flow;project.environment.design_return_temp_c=ret
            self.assertFalse(preview_pump_duty_v1(project).accepted);self.assertFalse(preview_pump_v1(project).ready)
            self.assertTrue(apply_pump_preview_basis_v1(project,pump_preview_draft_defaults_v1(project)))
            self.assertIs(project.hydronic_proportioned_basis_snapshot,snapshot);self.assertIs(project.hydronic_pump_duty_acceptance,acceptance)
        project.environment.design_flow_temp_c=75;project.environment.design_return_temp_c=65
        project.environment.external_design_temp_C=-10
        self.assertTrue(preview_pump_duty_v1(project).accepted)

    def test_commit_rejects_stale_or_missing_fluid(self):
        project=_project();_install_lengths(project);_,authority=live_authority(project)
        readiness=NS(return_arrangement_basis_ready=True,return_arrangement_basis_label='F&R',return_arrangement_basis_status='Reviewed',
            index_room_id=None,index_room_label='',terminal_room_id=None,terminal_room_label='',terminal_alignment_status='',
            basis_mode='',total_index_length_label='',nominal_gradient_label='')
        before=deepcopy(project.to_dict())
        with patch.object(snapshots,'build_proportioning_readiness_v1',return_value=readiness):
            result=snapshots.build_proportioned_basis_snapshot_v1(project,hydraulic_input_authority=authority)
            self.assertTrue(result.ready,result.blockers);self.assertEqual(before,project.to_dict())
            project.environment.design_flow_temp_c-=5
            self.assertFalse(snapshots.build_proportioned_basis_snapshot_v1(project,hydraulic_input_authority=authority).ready)
            self.assertFalse(snapshots.build_proportioned_basis_snapshot_v1(project,hydraulic_input_authority=replace(authority,fluid_basis=None)).ready)

    def test_resize_rebuild_preserves_fluid_and_stale_commit_is_atomic(self):
        # Synthetic numeric fixture isolates the existing atomic handoff;
        # actual resized arithmetic is independently checked above.
        from HVAC.dev.test_hs61h2a_atomic_pipe_schedule_commit_handoff_v1 import _fixtures, _Project, _adapter, module
        from HVAC.hydronics.proportioning.proportioned_pipe_resizing_schedule_acceptance_intent_v1 import build_proportioned_pipe_resizing_schedule_fingerprint_v1
        snapshot,material,resolved,projection,reconciliation=_fixtures()
        fluid=build_water_hydraulic_basis_v1(75,65)
        snapshot=replace(snapshot,hydraulic_input_authority=replace(snapshot.hydraulic_input_authority,fluid_basis=fluid))
        projection=replace(projection,fluid_basis=fluid)
        from HVAC.core.environment_state import EnvironmentStateV1
        project=_Project(snapshot=snapshot,material=material,acceptance_intent=object(),valve_intent=object())
        project.environment=EnvironmentStateV1()
        adapter,changed,_,refreshes=_adapter(project,projection,reconciliation)
        fingerprint=build_proportioned_pipe_resizing_schedule_fingerprint_v1(resized_hydraulics=projection,resized_point_reconciliation=reconciliation)
        different=replace(projection,fluid_basis=build_water_hydraulic_basis_v1(80,60))
        self.assertNotEqual(fingerprint,build_proportioned_pipe_resizing_schedule_fingerprint_v1(resized_hydraulics=different,resized_point_reconciliation=reconciliation))
        with patch.object(module,'resolve_proportioned_pipe_resizing_schedule_acceptance_v1',return_value=resolved):
            project.environment.design_flow_temp_c=80
            self.assertFalse(adapter.commit_proportioned_pipe_schedule_v1())
            self.assertIs(project.hydronic_proportioned_basis_snapshot,snapshot)
            self.assertEqual(changed.calls,0)
            project.environment.design_flow_temp_c=75
            self.assertTrue(adapter.commit_proportioned_pipe_schedule_v1())
        self.assertEqual(project.hydronic_proportioned_basis_snapshot.hydraulic_input_authority.fluid_basis,fluid)
        self.assertEqual(project.hydronic_proportioned_basis_snapshot.status,'COMMITTED_RESIZED_HYDRAULICS')
        self.assertEqual(changed.calls,1)

if __name__=='__main__':unittest.main()
