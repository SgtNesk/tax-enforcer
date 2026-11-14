"""Durable advisory case store: SQLite WAL, append-only hash-linked audit log.

Never issues, notifies, collects, or authorizes real administrative acts.
"""
import hashlib
import hmac
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .engine import evaluate_event

SCHEMA = '''
CREATE TABLE IF NOT EXISTS cases (
 id TEXT PRIMARY KEY, state TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL,
 revision INTEGER NOT NULL, event TEXT NOT NULL, from_state TEXT NOT NULL,
 to_state TEXT NOT NULL, evidence_json TEXT NOT NULL, actor TEXT NOT NULL,
 occurred_at TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL,
 FOREIGN KEY(case_id) REFERENCES cases(id), UNIQUE(case_id, revision)
);
'''

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

def digest(previous_hash, payload):
    return hashlib.sha256((previous_hash + '\n' + canonical(payload)).encode()).hexdigest()

class ConflictError(Exception):
    pass

class NotFoundError(Exception):
    pass

class CaseStore:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as con:
            con.executescript(SCHEMA)

    @contextmanager
    def connection(self):
        con = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        con.execute('PRAGMA busy_timeout=5000')
        con.execute('PRAGMA journal_mode=WAL')
        try:
            yield con
        finally:
            con.close()

    def create(self, case_id=None):
        case_id = case_id or str(uuid.uuid4())
        if not isinstance(case_id, str) or not 1 <= len(case_id) <= 100 or not all(c.isalnum() or c in '-_' for c in case_id):
            raise ValueError('Case ID must be 1-100 alphanumeric, underscore or dash characters')
        now = utcnow()
        with self.connection() as con:
            try:
                con.execute('INSERT INTO cases(id,state,revision,created_at,updated_at) VALUES(?,?,?,?,?)', (case_id,'detected',0,now,now))
            except sqlite3.IntegrityError as exc:
                raise ConflictError('Case already exists') from exc
        return self.get(case_id)

    def get(self, case_id):
        with self.connection() as con:
            row = con.execute('SELECT * FROM cases WHERE id=?',(case_id,)).fetchone()
            if row is None:
                raise NotFoundError('Case not found')
            return dict(row)

    def history(self, case_id):
        self.get(case_id)
        with self.connection() as con:
            rows = con.execute('SELECT * FROM events WHERE case_id=? ORDER BY revision', (case_id,)).fetchall()
        return [dict(row) for row in rows]

    def apply(self, case_id, event, evidence_refs, actor, expected_revision, human_approved=False):
        if not isinstance(expected_revision, int) or isinstance(expected_revision, bool) or expected_revision < 0:
            raise ValueError('expected_revision must be a non-negative integer')
        if not isinstance(actor, str) or not 1 <= len(actor) <= 100 or not all(c.isalnum() or c in '-_.' for c in actor):
            raise ValueError('Invalid actor identifier')
        with self.connection() as con:
            con.execute('BEGIN IMMEDIATE')
            try:
                row = con.execute('SELECT * FROM cases WHERE id=?', (case_id,)).fetchone()
                if row is None:
                    raise NotFoundError('Case not found')
                if row['revision'] != expected_revision:
                    raise ConflictError('Revision mismatch: refresh case before retrying')
                result = evaluate_event({'case_id':case_id, 'current_state':row['state'], 'event':event,
                                         'evidence_refs':evidence_refs, 'human_approved':human_approved})
                if result['status'] != 'simulation_only':
                    return {'committed':False, 'decision':result}
                previous = con.execute('SELECT event_hash FROM events WHERE case_id=? ORDER BY revision DESC LIMIT 1',(case_id,)).fetchone()
                previous_hash = previous['event_hash'] if previous else 'GENESIS'
                now = utcnow()
                payload = {'case_id':case_id,'revision':expected_revision+1,'event':event,
                           'from_state':row['state'],'to_state':result['proposed_state'],
                           'evidence_refs':evidence_refs,'actor':actor,'occurred_at':now}
                event_hash = digest(previous_hash,payload)
                con.execute('INSERT INTO events(case_id,revision,event,from_state,to_state,evidence_json,actor,occurred_at,previous_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?)',
                            (case_id,payload['revision'],event,row['state'],payload['to_state'],canonical(evidence_refs),actor,now,previous_hash,event_hash))
                con.execute('UPDATE cases SET state=?,revision=?,updated_at=? WHERE id=?',
                            (payload['to_state'],payload['revision'],now,case_id))
                con.execute('COMMIT')
                return {'committed':True,'case':{'id':case_id,'state':payload['to_state'],'revision':payload['revision']},'event_hash':event_hash,
                        'notice':'Internal simulation only; no administrative act was issued.'}
            except Exception:
                con.execute('ROLLBACK')
                raise

    def verify(self, case_id):
        events = self.history(case_id)
        prev = 'GENESIS'
        for i, event in enumerate(events, 1):
            payload = {'case_id':event['case_id'],'revision':event['revision'],'event':event['event'],
                       'from_state':event['from_state'],'to_state':event['to_state'],
                       'evidence_refs':json.loads(event['evidence_json']), 'actor':event['actor'],
                       'occurred_at':event['occurred_at']}
            if event['revision'] != i or not hmac.compare_digest(event['previous_hash'],prev) or not hmac.compare_digest(event['event_hash'],digest(prev,payload)):
                return {'valid':False,'checked_events':i-1,'error':'Audit chain mismatch'}
            prev = event['event_hash']
        current = self.get(case_id)
        if current['revision'] != len(events) or current['state'] != (events[-1]['to_state'] if events else 'detected'):
            return {'valid':False,'checked_events':len(events),'error':'Case state mismatch'}
        return {'valid':True,'checked_events':len(events),'head_hash':prev,
                'warning':'Hash chaining detects accidental modification, not a privileged attacker rewriting the entire database.'}
