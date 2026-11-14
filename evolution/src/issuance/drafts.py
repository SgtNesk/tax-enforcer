"""Evidence-backed, non-binding notice drafts. No identity lookup or delivery."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from html import escape
from io import BytesIO
import json
import re
from uuid import uuid4

PLATE = re.compile(r'^[A-Z0-9 -]{4,12}$')

class DraftValidationError(ValueError):
    pass

def build_draft(payload: dict) -> dict:
    """Generate a traceable review draft, not an administrative act."""
    required = ('event_time', 'location', 'violation_description', 'legal_reference', 'evidence_refs', 'reviewer')
    for key in required:
        if not payload.get(key):
            raise DraftValidationError(f'Missing required field: {key}')
    plate = str(payload.get('plate', '')).strip().upper()
    if not PLATE.fullmatch(plate):
        raise DraftValidationError('Invalid or missing plate format')
    refs = payload['evidence_refs']
    if not isinstance(refs, list) or not refs or len(refs) > 30 or any(not isinstance(r,str) or not re.fullmatch(r'[a-zA-Z0-9_./:-]{3,200}',r) for r in refs):
        raise DraftValidationError('At least one valid evidence reference is required')
    try:
        timestamp = datetime.fromisoformat(str(payload['event_time']).replace('Z','+00:00'))
        if timestamp.tzinfo is None:
            raise ValueError()
    except ValueError as exc:
        raise DraftValidationError('event_time must include a timezone') from exc
    if timestamp > datetime.now(timezone.utc):
        raise DraftValidationError('Event time cannot be in the future')
    try:
        amount = Decimal(str(payload.get('proposed_amount','0')))
        if not amount.is_finite() or amount < 0 or amount > 10000000 or amount.as_tuple().exponent < -2:
            raise ValueError()
    except (InvalidOperation, ValueError) as exc:
        raise DraftValidationError('Invalid proposed_amount') from exc
    for key in ('location','violation_description','legal_reference','reviewer'):
        if not isinstance(payload[key],str) or not 2 <= len(payload[key].strip()) <= 1000:
            raise DraftValidationError(f'Invalid {key}')
    body = {
        'draft_id': 'DRAFT-'+uuid4().hex[:16].upper(),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'event_time': timestamp.isoformat(), 'plate': plate,
        'location': payload['location'].strip(),
        'violation_description': payload['violation_description'].strip(),
        'legal_reference': payload['legal_reference'].strip(),
        'proposed_amount_eur': str(amount.quantize(Decimal('0.01'))),
        'evidence_refs': refs, 'reviewer': payload['reviewer'].strip(),
        'status': 'DRAFT_UNVERIFIED',
        'notice': 'BOZZA NON VALIDA COME VERBALE. Nessuna notifica, accertamento o sanzione emessa. Importo e norma da verificare da personale competente.',
    }
    canonical = json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    body['content_sha256'] = sha256(canonical.encode()).hexdigest()
    return body

def draft_pdf(draft: dict) -> bytes:
    """Printable draft with conspicuous watermark and safely wrapped text."""
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=(595,842), rightMargin=45,leftMargin=45,topMargin=50,bottomMargin=45)
    styles = getSampleStyleSheet()
    warning = ParagraphStyle('WarningDraft', parent=styles['Heading1'], textColor=colors.red, alignment=TA_CENTER)
    story = [Paragraph('BOZZA — NON È UN VERBALE', warning), Spacer(1,15)]
    fields = [('Identificativo', 'draft_id'), ('Evento', 'event_time'), ('Targa (da verificare)', 'plate'),
              ('Luogo', 'location'), ('Descrizione', 'violation_description'),
              ('Riferimento normativo (non verificato)', 'legal_reference'),
              ('Importo proposto (non verificato)', 'proposed_amount_eur'), ('Revisore dichiarato', 'reviewer')]
    for label,key in fields:
        story.append(Paragraph(f'<b>{escape(label)}:</b> {escape(str(draft[key]))}',styles['BodyText']))
        story.append(Spacer(1,9))
    story.append(Paragraph('<b>Riferimenti alle evidenze:</b> '+escape(', '.join(draft['evidence_refs'])),styles['BodyText']))
    story.append(Spacer(1,18))
    story.append(Paragraph(escape(draft['notice']),warning))
    story.append(Paragraph('SHA-256 del contenuto: '+escape(draft['content_sha256']),styles['BodyText']))
    document.build(story)
    return buffer.getvalue()
