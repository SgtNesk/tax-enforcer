import os
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

class CaseAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'OPERATOR_TOKEN':'x'*48,'CASE_DB_PATH':self.tmp.name+'/cases.db'})
        self.env.start()
        self.client = TestClient(app)
        self.headers = {'x-operator-token':'x'*48}

    def tearDown(self):
        self.client.close()
        self.env.stop()
        self.tmp.cleanup()

    def test_auth_required(self):
        self.assertEqual(self.client.post('/api/cases',json={'case_id':'a'}).status_code,403)

    def test_end_to_end(self):
        self.assertEqual(self.client.post('/api/cases',json={'case_id':'a'},headers=self.headers).status_code,201)
        r = self.client.post('/api/cases/a/events',json={'event':'submit_evidence','expected_revision':0},headers=self.headers)
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json()['committed'])
        self.assertEqual(self.client.get('/api/cases/a',headers=self.headers).json()['revision'],1)
        self.assertTrue(self.client.get('/api/cases/a/history',headers=self.headers).json()['verification']['valid'])

    def test_conflict(self):
        self.client.post('/api/cases',json={'case_id':'a'},headers=self.headers)
        self.client.post('/api/cases/a/events',json={'event':'submit_evidence','expected_revision':0},headers=self.headers)
        self.assertEqual(self.client.post('/api/cases/a/events',json={'event':'submit_evidence','expected_revision':0},headers=self.headers).status_code,409)

if __name__ == '__main__':
    unittest.main()
