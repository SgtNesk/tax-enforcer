import os
import tempfile
import unittest
from pathlib import Path
from src.lifecycle.store import CaseStore, ConflictError, NotFoundError

class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / 'cases.db')
        self.store = CaseStore(self.db)
        self.store.create('sample-001')

    def tearDown(self):
        self.temp.cleanup()

    def test_case_persists_across_instances(self):
        self.assertEqual(CaseStore(self.db).get('sample-001')['state'], 'detected')

    def test_transition_and_hash_chain(self):
        r = self.store.apply('sample-001','submit_evidence',[], 'operator1',0)
        self.assertTrue(r['committed'])
        self.assertEqual(CaseStore(self.db).get('sample-001')['state'], 'evidence_pending')
        self.assertTrue(self.store.verify('sample-001')['valid'])

    def test_revision_conflict(self):
        self.store.apply('sample-001','submit_evidence',[], 'operator1',0)
        with self.assertRaises(ConflictError):
            self.store.apply('sample-001','submit_evidence',[], 'operator1',0)

    def test_human_gate_is_not_persisted(self):
        self.store.apply('sample-001','submit_evidence',[], 'operator1',0)
        r = self.store.apply('sample-001','evidence_verified',['proof-1'],'operator1',1)
        self.assertFalse(r['committed'])
        self.assertEqual(self.store.get('sample-001')['revision'],1)

    def test_evidence_requirement(self):
        self.store.apply('sample-001','submit_evidence',[], 'operator1',0)
        r = self.store.apply('sample-001','evidence_verified',[],'operator1',1,True)
        self.assertFalse(r['committed'])

    def test_approved_transition(self):
        self.store.apply('sample-001','submit_evidence',[], 'operator1',0)
        r = self.store.apply('sample-001','evidence_verified',['evidence-001'],'operator1',1,True)
        self.assertTrue(r['committed'])
        self.assertTrue(self.store.verify('sample-001')['valid'])

    def test_detect_tampering(self):
        self.store.apply('sample-001','submit_evidence',[], 'operator1',0)
        with self.store.connection() as con:
            con.execute("UPDATE events SET actor='attacker' WHERE case_id='sample-001'")
        self.assertFalse(self.store.verify('sample-001')['valid'])

    def test_missing_case(self):
        with self.assertRaises(NotFoundError):
            self.store.get('missing')

    def test_duplicate_case(self):
        with self.assertRaises(ConflictError):
            self.store.create('sample-001')

    def test_invalid_actor(self):
        with self.assertRaises(ValueError):
            self.store.apply('sample-001','submit_evidence',[],'',0)

if __name__ == '__main__':
    unittest.main()
