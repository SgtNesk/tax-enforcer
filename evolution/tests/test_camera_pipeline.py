import hashlib
import tempfile
import unittest
from pathlib import Path
from src.camera.pipeline import CameraPipeline, CameraError

IMAGE = b'\xff\xd8\xff' + b'\x00' * 200
DATE = '2025-02-13T10:30:00+01:00'

class CameraPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pipeline = CameraPipeline(self.temp.name, ocr=lambda _: [{'plate':'AB123CD','confidence':0.91}])
    def ingest(self):
        return self.pipeline.ingest(IMAGE,camera_id='CAM_001',event_time=DATE,location='Via Roma, Milano')
    def test_ingest_and_persistence(self):
        record=self.ingest()
        self.assertEqual(record['evidence_sha256'],hashlib.sha256(IMAGE).hexdigest())
        self.assertEqual(self.pipeline.get(record['event_id'])['state'],'AWAITING_REVIEW')
        self.assertEqual(record['ocr_candidates'][0]['plate'],'AB123CD')
    def test_reject_non_image(self):
        with self.assertRaises(CameraError):
            self.pipeline.ingest(b'x'*200,camera_id='CAM_001',event_time=DATE,location='Via Roma')
    def test_reviewer_creates_draft(self):
        r=self.ingest()
        draft=self.pipeline.prepare_draft(r['event_id'],reviewer='Operator 01',verified_plate='AB123CD',violation_description='Possible red light violation',legal_reference='To be verified',proposed_amount='100.00')
        self.assertEqual(draft['status'],'DRAFT_UNVERIFIED')
        self.assertEqual(self.pipeline.get(r['event_id'])['state'],'DRAFT_PREPARED')
        with self.assertRaises(CameraError):
            self.pipeline.prepare_draft(r['event_id'],reviewer='Operator 01',verified_plate='AB123CD',violation_description='Possible red light violation',legal_reference='To be verified',proposed_amount='100.00')
    def test_detect_evidence_tampering(self):
        r=self.ingest()
        Path(self.pipeline.get(r['event_id'])['evidence_path']).write_bytes(b'changed')
        with self.assertRaises(CameraError):
            self.pipeline.prepare_draft(r['event_id'],reviewer='Operator 01',verified_plate='AB123CD',violation_description='Possible red light violation',legal_reference='To be verified',proposed_amount='100.00')
    def test_ocr_error_is_not_accusation(self):
        p=CameraPipeline(self.temp.name,ocr=lambda _: 1/0)
        r=p.ingest(IMAGE,camera_id='CAM_001',event_time=DATE,location='Via Roma')
        self.assertEqual(r['ocr_candidates'],[])
