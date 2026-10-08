"""H-S73-B1: frozen route identity compatibility; no GUI or project writes.

Run: PYTHONPATH=. python HVAC/dev/test_hs73b1_pump_route_identity_v1.py
Optionally append --project /path/to/project.json to check a saved snapshot
using the real snapshot loader. This option reads only; it never saves.
"""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from HVAC.hydronics.pumps import pump_preview_controller_v1 as controller
from HVAC.fluid.water_properties_v1 import build_water_hydraulic_basis_v1
from HVAC.core.environment_state import EnvironmentStateV1
FLUID = build_water_hydraulic_basis_v1(75, 65)


class PumpRouteIdentityTests(unittest.TestCase):
    def setUp(self):
        self.ids = ('leg-001-primary-subleg', 'leg-001-subleg-b',
                    'leg-002-primary-subleg', 'leg-002-subleg-b')
        self.members = ('leg-001:leg-001-primary-subleg', 'leg-001:leg-001-subleg-b',
                        'leg-002:leg-002-primary-subleg', 'leg-002:leg-002-subleg-b')
        self.section = NS(section_id='common-main-to-leg-001-section-001',
                          section_scope='common_main', order=1,
                          route_ids=self.members, carried_flow_kg_s=0.34928229665071775)
        self.authority = NS(fluid_basis=FLUID, sections=(self.section,), routes=tuple(
            NS(route_id=key, route_label=key, chosen_pressure_drop_Pa=dp)
            for key, dp in zip(self.ids, (43702.0, 38160.9, 40282.4, 68089.0))))
        self.project = NS(environment=EnvironmentStateV1(), hydronic_proportioned_basis_snapshot=NS(hydraulic_input_authority=self.authority),
                          hydronic_pump_preview_basis=None)
        # Deliberately isolate identity selection from snapshot validation,
        # which is unchanged and covered by the existing H-S73-A tests.
        self.mock = patch.object(controller, '_snapshot_evidence',
                                 side_effect=lambda snapshot: (self.authority, 'test-fingerprint', []))
        self.mock.start()
        self.addCleanup(self.mock.stop)

    def test_qualified_and_exact_membership_have_identical_flow(self):
        original = copy.deepcopy(self.authority)
        for members in (self.members, self.ids):
            self.section.route_ids = members
            result = controller.preview_pump_v1(self.project)
            self.assertEqual(result.mass_flow_kg_s, self.section.carried_flow_kg_s)
            self.assertEqual(result.flow_section_id, self.section.section_id)
            self.assertEqual(result.controlling_route_ids, (self.ids[-1],))
            self.assertEqual(result.pipework_pressure_Pa, 68089.0)
            self.assertEqual(result.blockers, ('Enter and apply an explicit preview basis; no density or allowances are assumed.',))
            self.assertIsNone(self.project.hydronic_pump_preview_basis)
        self.section.route_ids = self.members
        self.assertEqual(vars(self.authority), vars(original))

    def test_missing_unknown_duplicate_and_ambiguous_routes_block(self):
        bad_memberships = (self.members[:-1], self.members + ('leg-003:unknown',),
                           self.members + (self.members[0],),
                           (self.ids[0],) + self.members,
                           ('other-leg:' + self.ids[0],) + self.members,
                           ('a:b:' + self.ids[0],) + self.members[1:])
        for members in bad_memberships:
            with self.subTest(members=members):
                self.section.route_ids = members
                self.assertIsNone(controller.preview_pump_v1(self.project).mass_flow_kg_s)
        self.assertFalse(controller._section_covers_committed_routes_v1(
            ('leg:r', 'r'), {'leg:r', 'r'}))

    def test_first_common_main_still_must_be_unique_positive_and_complete(self):
        for field, value in (('order', 2), ('section_scope', 'leg_entry'),
                             ('carried_flow_kg_s', 0), ('carried_flow_kg_s', float('nan'))):
            old = getattr(self.section, field)
            setattr(self.section, field, value)
            self.assertIsNone(controller.preview_pump_v1(self.project).mass_flow_kg_s)
            setattr(self.section, field, old)
        self.authority.sections = (self.section, copy.deepcopy(self.section))
        self.assertIsNone(controller.preview_pump_v1(self.project).mass_flow_kg_s)
        self.authority.sections = ()
        self.assertIsNone(controller.preview_pump_v1(self.project).mass_flow_kg_s)

    def test_apply_remains_explicit_and_stale_basis_blocks(self):
        snapshot = self.project.hydronic_proportioned_basis_snapshot
        payload = dict(density_kg_m3=FLUID.density_kg_m3, additional_common_loss_Pa=0,
                       head_margin_percent=0, source_note='Synthetic test basis only')
        self.assertEqual(controller.apply_pump_preview_basis_v1(self.project, payload), ())
        result = controller.preview_pump_v1(self.project)
        self.assertTrue(result.ready)
        self.assertIs(self.project.hydronic_proportioned_basis_snapshot, snapshot)
        self.mock.stop()
        with patch.object(controller, '_snapshot_evidence', return_value=(self.authority, 'changed', [])):
            self.assertFalse(controller.preview_pump_v1(self.project).ready)
        self.mock.start()


def check_saved_project(path):
    """Read current real snapshot through its production persistence loader."""
    from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
        proportioned_basis_snapshot_from_dict_v1,
    )
    original = path.read_bytes()
    document = json.loads(original)
    payload = document.get('payload', document)
    snapshot = proportioned_basis_snapshot_from_dict_v1(payload['hydronic_proportioned_basis_snapshot'])
    project = NS(hydronic_proportioned_basis_snapshot=snapshot, hydronic_pump_preview_basis=None)
    result = controller.preview_pump_v1(project)
    if snapshot.hydraulic_input_authority.fluid_basis is None:
        assert any('Legacy' in b for b in result.blockers), result.blockers
    else:
        assert result.mass_flow_kg_s is not None, result.blockers
    assert path.read_bytes() == original
    print(f'READ ONLY saved snapshot: source={result.flow_section_id}; mass={result.mass_flow_kg_s} kg/s; blockers={result.blockers}')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--project':
        check_saved_project(Path(sys.argv[2]))
        sys.argv = sys.argv[:1]
    unittest.main()
