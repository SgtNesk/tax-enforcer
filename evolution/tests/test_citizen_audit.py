import unittest
from src.citizen_audit import audit_case

class AuditTests(unittest.TestCase):
    def test_exact_reconciliation(self):
        r = audit_case({'principal':'200','claimed_total':'1084','charges':[{'label':'Unverified additions','amount':'884'}]})
        self.assertTrue(r['arithmetic_matches'])
        self.assertTrue(r['review_required'])
    def test_unexplained_difference(self):
        r = audit_case({'principal':'200','claimed_total':'1084'})
        self.assertEqual(r['difference'], '884.00')
        self.assertTrue(r['needs_itemization'])
    def test_payments(self):
        r = audit_case({'principal':'200','claimed_total':'180','payments':[{'amount':'20'}]})
        self.assertTrue(r['arithmetic_matches'])
    def test_reject_negative(self):
        with self.assertRaises(ValueError):
            audit_case({'principal':'-1','claimed_total':'0'})
    def test_reject_nonfinite(self):
        with self.assertRaises(ValueError):
            audit_case({'principal':'NaN','claimed_total':'0'})

if __name__ == '__main__':
    unittest.main()
