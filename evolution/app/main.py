"""Citizen-first read-only analysis API. No uploads are persisted."""
import io
import json
import os
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware
from src.citizen_audit.engine import audit_case
from src.lifecycle.store import CaseStore, ConflictError, NotFoundError

app = FastAPI(title='Tax Enforcer — Lifecycle & Citizen Audit', version='0.3.0', docs_url='/api/docs')

@app.middleware('http')
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    return response

if os.getenv('APP_ENV') == 'production' and len(os.getenv('SESSION_SECRET', '')) < 32:
    raise RuntimeError('Production requires SESSION_SECRET of at least 32 characters')

app.add_middleware(SessionMiddleware, secret_key=os.getenv('SESSION_SECRET', 'development-only-do-not-use-in-production'),
                   https_only=os.getenv('APP_ENV') == 'production', same_site='lax', max_age=3600)
MAX_UPLOAD = 5 * 1024 * 1024

class CaseInput(BaseModel):
    case_id: str = Field(default='demo', max_length=100)
    principal: str
    claimed_total: str
    charges: list[dict] = Field(default_factory=list, max_length=500)
    payments: list[dict] = Field(default_factory=list, max_length=500)

@app.get('/health')
def health():
    return {'status': 'ok', 'version': '0.3.0'}

@app.get('/', response_class=HTMLResponse)
def index():
    return (Path(__file__).parent / 'index.html').read_text(encoding='utf-8')

@app.post('/api/audit')
def audit(payload: CaseInput):
    try:
        return audit_case(payload.model_dump())
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post('/api/extract')
async def extract(file: UploadFile = File(...)):
    """PDF text extraction only, with no OCR or AI guessing. User must confirm values."""
    if file.content_type != 'application/pdf' or not (file.filename or '').lower().endswith('.pdf'):
        raise HTTPException(415, 'Only PDF documents are supported')
    data = await file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, 'PDF exceeds 5 MB')
    if not data.startswith(b'%PDF-'):
        raise HTTPException(422, 'Invalid PDF header')
    try:
        import pymupdf
        doc = pymupdf.open(stream=data, filetype='pdf')
        if doc.needs_pass or doc.page_count > 30:
            raise HTTPException(422, 'Password-protected or over 30-page PDF')
        text = '\n'.join(page.get_text(sort=True) for page in doc)
        doc.close()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422, 'Unable to parse PDF')
    return {'text': text[:30000], 'truncated': len(text) > 30000,
            'notice': 'Extracted text is unverified. No values are automatically deemed legally valid.'}

# SPID is disabled unless configured with a real SP + IdP SAML configuration.
def spid_settings():
    config_path = os.getenv('SPID_SETTINGS_PATH', '')
    if not config_path or not Path(config_path).is_file():
        raise HTTPException(503, 'SPID not configured: accredited SP metadata and IdP trust required')
    try:
        from onelogin.saml2.settings import OneLogin_Saml2_Settings
        settings = json.loads(Path(config_path).read_text(encoding='utf-8'))
        check = OneLogin_Saml2_Settings(settings=settings, custom_base_path=str(Path(config_path).parent), sp_validation_only=False)
        errors = check.validate_metadata(check.get_sp_metadata())
        if errors:
            raise ValueError('Invalid SP metadata')
        return settings
    except (ImportError, ValueError, KeyError) as exc:
        raise HTTPException(503, 'Invalid or incomplete SPID configuration') from exc

def saml_request(request, post_data=None):
    return {'https': 'on' if request.url.scheme == 'https' else 'off',
            'http_host': request.headers.get('host', ''), 'server_port': str(request.url.port or (443 if request.url.scheme == 'https' else 80)),
            'script_name': request.url.path, 'get_data': dict(request.query_params), 'post_data': post_data or {}}

@app.get('/auth/spid/start')
def spid_start(request: Request):
    if os.getenv('APP_ENV') != 'production' or request.url.scheme != 'https':
        raise HTTPException(503, 'SPID requires HTTPS production configuration')
    settings = spid_settings()
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    auth = OneLogin_Saml2_Auth(saml_request(request), old_settings=settings)
    target = auth.login(return_to=str(request.base_url))
    request.session['saml_request_id'] = auth.get_last_request_id()
    return RedirectResponse(target, status_code=302)

@app.post('/auth/spid/acs')
async def spid_acs(request: Request):
    if os.getenv('APP_ENV') != 'production' or request.url.scheme != 'https':
        raise HTTPException(503, 'SPID requires HTTPS production configuration')
    settings = spid_settings()
    form = await request.form()
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    auth = OneLogin_Saml2_Auth(saml_request(request, dict(form)), old_settings=settings)
    request_id = request.session.pop('saml_request_id', None)
    if not request_id:
        raise HTTPException(401, 'Missing authentication request')
    auth.process_response(request_id=request_id)
    if auth.get_errors() or not auth.is_authenticated():
        raise HTTPException(401, 'Invalid SAML response')
    # Store minimal session state; do not put attributes or identity numbers in cookies.
    request.session['authenticated'] = True
    return RedirectResponse('/', status_code=303)

@app.get('/auth/status')
def auth_status(request: Request):
    return {'authenticated': request.session.get('authenticated') is True,
            'spid_configured': bool(os.getenv('SPID_SETTINGS_PATH') and Path(os.getenv('SPID_SETTINGS_PATH')).is_file())}

@app.post('/auth/logout')
def logout(request: Request):
    request.session.clear()
    return {'ok': True, 'note': 'Local session ended; IdP SLO is not configured'}

@app.get('/auth/spid/metadata', response_class=HTMLResponse)
def metadata():
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    settings = OneLogin_Saml2_Settings(settings=spid_settings(), sp_validation_only=False)
    return HTMLResponse(settings.get_sp_metadata(), media_type='application/samlmetadata+xml')


from src.lifecycle.engine import evaluate_event, get_workflow

class LifecycleInput(BaseModel):
    case_id: str = Field(min_length=1, max_length=100)
    current_state: str
    event: str
    evidence_refs: list[str] = Field(default_factory=list, max_length=50)
    human_approved: bool = False

@app.get('/api/lifecycle')
def lifecycle_schema():
    return get_workflow()

@app.post('/api/lifecycle/evaluate')
def lifecycle_evaluate(payload: LifecycleInput):
    try:
        return evaluate_event(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


# Persistent advisory workflow. Disabled by default. Explicit operator token required.
# SPID login alone is not an authorization to operate administrative cases.
from fastapi import Header, Depends
from typing import Optional

class CreateCaseInput(BaseModel):
    case_id: Optional[str] = Field(default=None, max_length=100)

class ApplyEventInput(BaseModel):
    event: str = Field(min_length=1, max_length=100)
    expected_revision: int = Field(ge=0)
    evidence_refs: list[str] = Field(default_factory=list, max_length=50)
    human_approved: bool = False


def operator_auth(x_operator_token: Optional[str] = Header(default=None)):
    import hmac
    configured = os.getenv('OPERATOR_TOKEN', '')
    if len(configured) < 32 or not x_operator_token or not hmac.compare_digest(configured, x_operator_token):
        raise HTTPException(403, 'Persistent case API disabled or unauthorized')
    return 'operator_demo'


def case_store():
    path = os.getenv('CASE_DB_PATH', '')
    if not path:
        raise HTTPException(503, 'Persistent case store not configured')
    return CaseStore(path)

@app.post('/api/cases', status_code=201)
def create_case(payload: CreateCaseInput, actor: str = Depends(operator_auth)):
    try:
        return case_store().create(payload.case_id)
    except ConflictError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@app.get('/api/cases/{case_id}')
def read_case(case_id: str, actor: str = Depends(operator_auth)):
    try:
        return case_store().get(case_id)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

@app.post('/api/cases/{case_id}/events')
def apply_case_event(case_id: str, payload: ApplyEventInput, actor: str = Depends(operator_auth)):
    try:
        return case_store().apply(case_id, payload.event, payload.evidence_refs, actor,
                                  payload.expected_revision, payload.human_approved)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@app.get('/api/cases/{case_id}/history')
def case_history(case_id: str, actor: str = Depends(operator_auth)):
    try:
        return {'events':case_store().history(case_id),'verification':case_store().verify(case_id)}
    except NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

# Non-binding notice drafts: restricted to operator token, never sends or issues acts.
from fastapi.responses import Response
from src.issuance.drafts import build_draft, draft_pdf, DraftValidationError

class DraftInput(BaseModel):
    plate: str = Field(min_length=4,max_length=20)
    event_time: str
    location: str = Field(min_length=2,max_length=1000)
    violation_description: str = Field(min_length=2,max_length=1000)
    legal_reference: str = Field(min_length=2,max_length=1000)
    evidence_refs: list[str] = Field(min_length=1,max_length=30)
    reviewer: str = Field(min_length=2,max_length=1000)
    proposed_amount: str = '0.00'

@app.post('/api/issuance/draft')
def create_notice_draft(payload: DraftInput, actor: str = Depends(operator_auth)):
    try:
        return build_draft(payload.model_dump())
    except DraftValidationError as exc:
        raise HTTPException(422,str(exc)) from exc

@app.post('/api/issuance/draft.pdf')
def create_notice_draft_pdf(payload: DraftInput, actor: str = Depends(operator_auth)):
    try:
        draft = build_draft(payload.model_dump())
        return Response(draft_pdf(draft),media_type='application/pdf',
                        headers={'Content-Disposition':'attachment; filename="tax-enforcer-draft.pdf"'})
    except DraftValidationError as exc:
        raise HTTPException(422,str(exc)) from exc
