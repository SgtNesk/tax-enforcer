import unittest
from src.lifecycle.engine import evaluate_event, get_workflow

class LifecycleTests(unittest.TestCase):
    def test_workflow_contains_refund(self):
        self.assertIn('refunded', get_workflow()['states'])
    def test_gated_notice(self):
        r=evaluate_event({'case_id':'demo','current_state':'notice_pending','event':'authorize_notice'})
        self.assertEqual(r['status'],'requires_human_approval')
        self.assertFalse(r['executed'])
    def test_requires_evidence(self):
        r=evaluate_event({'case_id':'demo','current_state':'notice_pending','event':'authorize_notice','human_approved':True})
        self.assertEqual(r['status'],'evidence_required')
    def test_approved_simulation_still_does_not_execute(self):
        r=evaluate_event({'case_id':'demo','current_state':'notice_pending','event':'authorize_notice','human_approved':True,'evidence_refs':['evidence:123']})
        self.assertEqual(r['status'],'simulation_only')
        self.assertFalse(r['executed'])
    def test_reject_invalid_transition(self):
        with self.assertRaises(ValueError):
            evaluate_event({'case_id':'demo','current_state':'detected','event':'authorize_refund'})
    def test_citizen_appeal(self):
        r=evaluate_event({'case_id':'demo','current_state':'notified','event':'request_review'})
        self.assertEqual(r['proposed_state'],'contested')
