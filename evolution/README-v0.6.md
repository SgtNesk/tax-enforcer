# Tax Enforcer Evolution v0.6 — camera-first

## Scope
Camera-triggered traffic infraction evidence pipeline. This is a demonstrator, **not** a certified enforcement platform.

## New in v0.6
`src.camera.CameraPipeline` provides local persistent intake of JPEG/PNG evidence (5 MB max), SHA-256 evidence hashing, camera identifier and timezone-aware event timestamp, injectable OCR candidate adapter, manual reviewer gate, integrity re-check, and structured non-binding PDF draft generation through `src.issuance.drafts`.

No automatic assumption of guilt: OCR is a suggestion, not a verified plate; a detected plate does not prove a violation. The reviewer must provide the confirmed plate, violation description, legal reference and proposed amount. Any OCR failure results in manual review.

## Example
```python
from src.camera import CameraPipeline
from src.issuance.drafts import draft_pdf
p = CameraPipeline('./local-private-data')
image = open('synthetic-camera.jpg','rb').read()
event = p.ingest(image, camera_id='CAM_001', event_time='2025-02-13T10:30:00+01:00', location='Via Roma, Milano')
print(event)
# After human review:
draft = p.prepare_draft(event['event_id'], reviewer='Reviewer 1', verified_plate='AB123CD', violation_description='Observed event pending legal validation', legal_reference='To be validated', proposed_amount='100.00')
open('draft.pdf','wb').write(draft_pdf(draft))
```

Run `python -m unittest discover -s tests -v`.

## Required before deployment
- Genuine camera integration, authenticated signed events, sensor calibration and chain of custody.
- Real image validation/decoding, malware screening, retention and GDPR/DPIA compliance; encryption at rest, access controls and deletion policy.
- Production OCR service, evaluated on realistic data and human verification.
- Authorized vehicle registry integration, validated violation-specific legal rules, qualified reviewers and official templates.
- Legally valid signature, transmission, receipt and notification integrations with authorities.
- PostgreSQL migrations, robust tenant isolation, IAM, SPID integration, observability, backups, pen testing and operational controls.

Existing prototype APIs, demo credentials and sample data must not be exposed to the public. Camera evidence files are private by default on local disk, but local disk permissions are not sufficient production security.
