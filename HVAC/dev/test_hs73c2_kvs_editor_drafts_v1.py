"""Real Qt editor: per-point drafts, exact-evidence expiry and project scope."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace as NS
import unittest
from PySide6.QtWidgets import QApplication
from HVAC.gui_v3.panels.hydronics_schematic_panel import HydronicsSchematicPanel
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import HydronicsSchematicPanelAdapter as Adapter
from HVAC.dev.test_hs62a_exact_kvs_duty_acceptance_freshness_v1 import _row as duty_row
from HVAC.dev.test_hs62b_exact_kvs_consequence_disposition_freshness_v1 import _row as consequence_row
from HVAC.dev.test_hs73b_pump_duty_v1 import fixture

APP = QApplication.instance() or QApplication([])


def rows(duty_change=False, consequence_change=False):
    duties = [replace(duty_row(), balancing_point_id=p) for p in ('a', 'b')]
    consequences = [replace(consequence_row(), balancing_point_id=p) for p in ('a', 'b')]
    if duty_change:
        duties[0] = replace(duties[0], controlled_circuit_dp_pa=12600.000001)
    if consequence_change:
        consequences[0] = replace(consequences[0], implied_valve_dp_pa=20250.000001)
    return Adapter._build_balancing_point_kvs_acceptance_editor_rows_v1(
        point_display_rows=[dict(balancing_point_id=p, required_kv='0.920') for p in ('a', 'b')],
        utilisation_evidence=NS(rows=duties),
        acceptance_resolution=NS(rows=[NS(balancing_point_id=p, accepted_kvs=1.0, accepted=True, status='Accepted', blockers=()) for p in ('a', 'b')]),
        consequence_evidence=NS(rows=consequences), disposition_resolution=NS(rows=[]),
    )


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.p = HydronicsSchematicPanel(); self.owner = NS()
        self.p.set_kvs_editor_project_v1(self.owner)
        self.r = rows(); self.refresh()
        self.point = self.p._point_kvs_acceptance_point_combo
        self.candidate = self.p._point_kvs_acceptance_candidate_combo
        self.disposition = self.p._kvs_consequence_disposition_combo
        self.calls = []
        self.p.set_balancing_point_kvs_acceptance_callback(self.calls.append)
        self.p.set_accepted_kvs_consequence_disposition_callback(self.calls.append)

    def tearDown(self):
        self.p.close(); self.p.deleteLater(); APP.processEvents()

    def choose(self, combo, value):
        index = combo.findData(value); self.assertGreaterEqual(index, 0)
        combo.setCurrentIndex(index)

    def refresh(self, value=None):
        self.p.set_balancing_point_kvs_acceptance_editor_rows(deepcopy(self.r if value is None else value))

    def test_two_points_refresh_reorder_no_implicit_actions(self):
        original = deepcopy(self.r)
        self.choose(self.candidate, 1.6); self.choose(self.disposition, 'kvs_revision_required')
        self.choose(self.point, 'b'); self.choose(self.candidate, 2.5)
        self.choose(self.disposition, 'approved_for_product_search')
        self.refresh(list(reversed(self.r)))
        self.assertEqual(self.point.currentData(), 'b')
        self.assertEqual(self.candidate.currentData(), 2.5)
        for _ in range(3): self.refresh()
        self.choose(self.point, 'a')
        self.assertEqual(self.candidate.currentData(), 1.6)
        self.assertEqual(self.disposition.currentData(), 'kvs_revision_required')
        self.assertIn('Unsubmitted choice; saved Kvs 1.', self.p._point_kvs_acceptance_status_label.text())
        self.assertIn('Unsubmitted choice.', self.p._kvs_consequence_disposition_status_label.text())
        self.assertEqual(self.calls, []); self.assertEqual(self.r, original)
        self.assertEqual(vars(self.owner), {})

    def test_placeholder_is_preserved(self):
        self.choose(self.candidate, None)
        self.choose(self.point, 'b'); self.choose(self.point, 'a'); self.refresh()
        self.assertIsNone(self.candidate.currentData())
        self.assertFalse(self.p._point_kvs_acceptance_apply_button.isEnabled())

    def test_exact_duty_change_expires_hidden_point_without_revival(self):
        self.choose(self.candidate, 1.6); self.choose(self.disposition, 'kvs_revision_required')
        self.choose(self.point, 'b'); self.choose(self.candidate, 2.5)
        changed = rows(duty_change=True)
        self.assertEqual(changed[0]['required_kv'], self.r[0]['required_kv'])
        self.assertNotEqual(changed[0]['draft_duty_fingerprint'], self.r[0]['draft_duty_fingerprint'])
        self.refresh(changed); self.refresh()
        self.assertEqual(self.candidate.currentData(), 2.5)
        self.choose(self.point, 'a')
        self.assertEqual(self.candidate.currentData(), 1.0)
        self.assertIsNone(self.disposition.currentData())

    def test_consequence_change_preserves_candidate(self):
        self.choose(self.candidate, 2.5); self.choose(self.disposition, 'kvs_revision_required')
        self.refresh(rows(consequence_change=True))
        self.assertEqual(self.candidate.currentData(), 2.5)
        self.assertIsNone(self.disposition.currentData())

    def test_removed_point_missing_evidence_and_project_lifecycle(self):
        self.choose(self.candidate, 2.5)
        self.refresh([self.r[1]]); self.refresh(); self.choose(self.point, 'a')
        self.assertEqual(self.candidate.currentData(), 1.0)
        self.choose(self.candidate, 2.5)
        changed = deepcopy(self.r); changed[0]['draft_duty_fingerprint'] = ''
        self.refresh(changed); self.refresh()
        self.assertEqual(self.candidate.currentData(), 1.0)
        self.choose(self.candidate, 2.5)
        self.p.set_kvs_editor_project_v1(self.owner); self.refresh()
        self.assertEqual(self.candidate.currentData(), 2.5)
        self.p.set_kvs_editor_project_v1(NS()); self.refresh()
        self.assertEqual(self.candidate.currentData(), 1.0)

    def test_accept_clear_and_unsuccessful_action(self):
        self.choose(self.point, 'b'); self.choose(self.candidate, 2.5)
        self.p._point_kvs_acceptance_apply_button.click()
        self.assertEqual(self.calls, [dict(action='accept', balancing_point_id='b', accepted_kvs=2.5)])
        self.refresh()  # no saved evidence update, e.g. rejected action
        self.assertEqual(self.candidate.currentData(), 2.5)
        changed = deepcopy(self.r); changed[1]['accepted_kvs'] = 2.5
        self.refresh(changed); self.choose(self.candidate, 1.6)
        self.p._point_kvs_acceptance_clear_button.click()
        changed[1]['accepted_kvs'] = None; changed[1]['accepted'] = False
        self.refresh(changed); self.assertIsNone(self.candidate.currentData())
        self.assertEqual(self.calls[-1], dict(action='clear', balancing_point_id='b'))

    def test_disposition_actions_preserve_candidate_draft(self):
        self.choose(self.candidate, 2.5); self.choose(self.disposition, 'kvs_revision_required')
        self.p._kvs_consequence_disposition_apply_button.click()
        self.assertEqual(self.calls[-1], dict(action='set', balancing_point_id='a', disposition='kvs_revision_required'))
        changed = deepcopy(self.r); changed[0]['consequence_disposition'] = 'kvs_revision_required'
        self.refresh(changed); self.assertEqual(self.candidate.currentData(), 2.5)
        self.choose(self.disposition, 'approved_for_product_search')
        self.p._kvs_consequence_disposition_clear_button.click()
        self.refresh(); self.assertIsNone(self.disposition.currentData())
        self.assertEqual(self.candidate.currentData(), 2.5)

    def test_real_adapter_binds_project_before_projection(self):
        adapter = Adapter(panel=self.p, project_state=fixture(), context=None)
        self.refresh(); self.choose(self.candidate, 2.5)
        # Stop expensive projections after the real refresh's project-binding step.
        def after_binding():
            self.assertIs(self.p._kvs_editor_project_v1, adapter._project_state)
            raise StopIteration
        adapter._refresh_pump_preview_v1 = after_binding
        with self.assertRaises(StopIteration): adapter.refresh()
        self.refresh(); self.assertEqual(self.candidate.currentData(), 2.5)
        with self.assertRaises(StopIteration): adapter.set_project_state(fixture())
        self.refresh(); self.assertEqual(self.candidate.currentData(), 1.0)


if __name__ == '__main__':
    unittest.main()
