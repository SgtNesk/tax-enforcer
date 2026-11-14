"""Deterministic advisory workflow. No persistence, enforcement or legally binding action."""
from datetime import datetime, timezone

TRANSITIONS = {
    'detected': {'submit_evidence': 'evidence_pending'},
    'evidence_pending': {'evidence_verified': 'legal_review', 'evidence_rejected': 'closed_no_violation'},
    'legal_review': {'propose_notice': 'notice_pending', 'dismiss': 'closed_no_violation'},
    'notice_pending': {'authorize_notice': 'notified', 'reject_notice': 'legal_review'},
    'notified': {'request_review': 'contested', 'record_payment': 'reconciliation', 'request_installments': 'payment_plan_review'},
    'contested': {'accept_appeal': 'annulment_pending', 'reject_appeal': 'notified'},
    'annulment_pending': {'authorize_annulment': 'annulled'},
    'payment_plan_review': {'approve_plan': 'installments', 'reject_plan': 'notified'},
    'installments': {'record_payment': 'reconciliation'},
    'reconciliation': {'confirm_settlement': 'closed_paid', 'refund_needed': 'refund_review'},
    'refund_review': {'authorize_refund': 'refunded'},
}
HUMAN_GATED = {'authorize_notice','authorize_annulment','accept_appeal','reject_appeal',
               'approve_plan','reject_plan','confirm_settlement','authorize_refund','dismiss',
               'evidence_verified','evidence_rejected'}

def get_workflow():
    return {'states': sorted(set(TRANSITIONS) | {x for t in TRANSITIONS.values() for x in t.values()}),
            'transitions': TRANSITIONS, 'human_gated_events': sorted(HUMAN_GATED),
            'mode': 'advisory_only', 'persisted': False}

def evaluate_event(data):
    state = data.get('current_state')
    event = data.get('event')
    if state not in TRANSITIONS or event not in TRANSITIONS[state]:
        raise ValueError('Unsupported state/event transition')
    refs = data.get('evidence_refs', [])
    if not isinstance(refs, list) or any(not isinstance(x, str) or not x.strip() or len(x)>250 for x in refs):
        raise ValueError('Evidence references must be nonempty strings of max 250 chars')
    if event in HUMAN_GATED and not data.get('human_approved', False):
        return {'case_id': data['case_id'], 'status': 'requires_human_approval',
                'current_state': state, 'proposed_state': TRANSITIONS[state][event],
                'event': event, 'executed': False}
    if event in {'evidence_verified','authorize_notice','accept_appeal','authorize_annulment','authorize_refund'} and not refs:
        return {'case_id': data['case_id'], 'status': 'evidence_required',
                'current_state': state, 'proposed_state': TRANSITIONS[state][event], 'executed': False}
    return {'case_id': data['case_id'], 'status': 'simulation_only',
            'current_state': state, 'proposed_state': TRANSITIONS[state][event],
            'event': event, 'executed': False, 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'evidence_refs': refs}
