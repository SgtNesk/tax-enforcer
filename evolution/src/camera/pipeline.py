"""Camera evidence ingestion -> OCR candidates -> human-reviewed draft.

No vehicle registry lookup, automatic guilt determination, official issuance or delivery.
"""
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from src.issuance.drafts import build_draft

class CameraError(ValueError):
    pass

class CameraPipeline:
    def __init__(self, root, ocr=None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.evidence = self.root / 'evidence'
        self.evidence.mkdir(exist_ok=True, mode=0o700)
        self.db = self.root / 'camera.sqlite3'
        self.ocr = ocr
        with self._connect() as con:
            con.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, camera_id TEXT NOT NULL, event_time TEXT NOT NULL, location TEXT NOT NULL, evidence_sha256 TEXT NOT NULL, evidence_path TEXT NOT NULL, candidates_json TEXT NOT NULL, state TEXT NOT NULL, draft_json TEXT)')

    def _connect(self):
        con = sqlite3.connect(self.db)
        con.row_factory = sqlite3.Row
        return con

    def ingest(self, image: bytes, *, camera_id: str, event_time: str, location: str):
        if not isinstance(image, bytes) or not 100 <= len(image) <= 5_000_000:
            raise CameraError('Image must be 100 bytes to 5 MB')
        if not (image.startswith(b'\xff\xd8\xff') or image.startswith(b'\x89PNG\r\n\x1a\n')):
            raise CameraError('Only JPEG and PNG evidence is supported')
        if not re.fullmatch(r'[A-Za-z0-9_-]{3,80}', camera_id):
            raise CameraError('Invalid camera identifier')
        if not isinstance(location, str) or not 3 <= len(location.strip()) <= 300:
            raise CameraError('Invalid location')
        try:
            dt = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
            if dt.tzinfo is None or dt > datetime.now(timezone.utc):
                raise ValueError()
        except (ValueError, AttributeError):
            raise CameraError('Event timestamp must be timezone-aware and not in future')
        digest = hashlib.sha256(image).hexdigest()
        event_id = 'CAM-' + uuid4().hex.upper()
        ext = '.jpg' if image.startswith(b'\xff') else '.png'
        dest = self.evidence / (event_id + ext)
        with dest.open('xb') as f:
            os.chmod(dest, 0o600)
            f.write(image)
        candidates = []
        if self.ocr is not None:
            try:
                raw = self.ocr(image)
                if not isinstance(raw, list):
                    raise TypeError('OCR must return a list')
                for item in raw[:20]:
                    plate = str(item.get('plate','')).upper().replace(' ', '')
                    confidence = float(item.get('confidence', 0))
                    if re.fullmatch(r'[A-Z0-9]{4,12}', plate) and 0 <= confidence <= 1:
                        candidates.append({'plate':plate,'confidence':confidence})
            except Exception:
                # Evidence is retained for manual review; OCR errors cannot create an accusation.
                candidates = []
        with self._connect() as con:
            con.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?)',
                        (event_id,camera_id,dt.isoformat(),location.strip(),digest,str(dest),json.dumps(candidates),'AWAITING_REVIEW',None))
        return {'event_id':event_id,'evidence_sha256':digest,'ocr_candidates':candidates,'state':'AWAITING_REVIEW'}

    def get(self, event_id):
        with self._connect() as con:
            row = con.execute('SELECT * FROM events WHERE id=?',(event_id,)).fetchone()
        if row is None:
            raise CameraError('Unknown event')
        return dict(row)

    def prepare_draft(self, event_id, *, reviewer, verified_plate, violation_description, legal_reference, proposed_amount):
        event = self.get(event_id)
        if event['state'] != 'AWAITING_REVIEW':
            raise CameraError('Event is already processed')
        if not Path(event['evidence_path']).exists():
            raise CameraError('Evidence unavailable')
        actual = hashlib.sha256(Path(event['evidence_path']).read_bytes()).hexdigest()
        if actual != event['evidence_sha256']:
            raise CameraError('Evidence integrity check failed')
        draft = build_draft({'event_time':event['event_time'],'location':event['location'],
            'plate':verified_plate,'violation_description':violation_description,
            'legal_reference':legal_reference,'proposed_amount':proposed_amount,
            'evidence_refs':[event['evidence_sha256']],'reviewer':reviewer})
        with self._connect() as con:
            cur=con.execute("UPDATE events SET state='DRAFT_PREPARED',draft_json=? WHERE id=? AND state='AWAITING_REVIEW'",(json.dumps(draft),event_id))
            if cur.rowcount != 1:
                raise CameraError('Concurrent review conflict')
        return draft
