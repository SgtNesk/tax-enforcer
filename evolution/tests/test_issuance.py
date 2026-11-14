import io
from datetime import datetime, timedelta, timezone
import pytest
from src.issuance.drafts import build_draft, draft_pdf, DraftValidationError

def sample():
    return {'plate':'AB123CD','event_time':(datetime.now(timezone.utc)-timedelta(days=1)).isoformat(),
            'location':'Luogo dimostrativo','violation_description':'Evento di prova, non accertato',
            'legal_reference':'Riferimento da verificare','evidence_refs':['evidence:sample-001'],
            'reviewer':'Operatore test','proposed_amount':'200.00'}

def test_draft_is_nonbinding_and_hashed():
    d=build_draft(sample())
    assert d['status']=='DRAFT_UNVERIFIED' and len(d['content_sha256'])==64
    assert 'Nessuna notifica' in d['notice']

def test_pdf_is_readable():
    import pymupdf
    pdf=draft_pdf(build_draft(sample()))
    doc=pymupdf.open(stream=pdf,filetype='pdf')
    assert 'NON' in doc[0].get_text() and 'BOZZA' in doc[0].get_text()
    doc.close()

def test_reject_future_event():
    p=sample();p['event_time']=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()
    with pytest.raises(DraftValidationError):build_draft(p)

def test_reject_bad_plate():
    p=sample();p['plate']='../../etc'
    with pytest.raises(DraftValidationError):build_draft(p)

def test_reject_missing_evidence():
    p=sample();p['evidence_refs']=[]
    with pytest.raises(DraftValidationError):build_draft(p)

def test_reject_infinite_amount():
    p=sample();p['proposed_amount']='Infinity'
    with pytest.raises(DraftValidationError):build_draft(p)

def test_reject_naive_datetime():
    p=sample();p['event_time']='2025-02-13T10:30:00'
    with pytest.raises(DraftValidationError):build_draft(p)
