"""Arithmetic reconciliation only; does not decide legal enforceability."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date

CENT = Decimal('0.01')

def money(value):
    try:
        result = Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('Invalid monetary amount') from exc
    if not result.is_finite() or result < 0:
        raise ValueError('Amounts must be finite and nonnegative')
    return result

def audit_case(case):
    """Return an explainable reconciliation report for a manually supplied case.

    Input: {case_id, principal, claimed_total, charges:[{label,amount,date?,source?}],
            payments:[{amount,date?,source?}]}. All figures are in EUR.
    """
    if not isinstance(case, dict):
        raise ValueError('Case must be an object')
    principal = money(case['principal'])
    claimed = money(case['claimed_total'])
    charges = case.get('charges', [])
    payments = case.get('payments', [])
    if not isinstance(charges, list) or not isinstance(payments, list):
        raise ValueError('Charges and payments must be arrays')
    def check(items, kind):
        out = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f'{kind}[{i}] must be an object')
            if item.get('date'):
                date.fromisoformat(item['date'])
            out.append({'label': str(item.get('label', kind)), 'amount': str(money(item['amount'])),
                        'date': item.get('date'), 'source': item.get('source')})
        return out
    charges = check(charges, 'charge')
    payments = check(payments, 'payment')
    charges_total = sum((Decimal(x['amount']) for x in charges), Decimal('0'))
    payments_total = sum((Decimal(x['amount']) for x in payments), Decimal('0'))
    reconstructed = principal + charges_total - payments_total
    discrepancy = claimed - reconstructed
    return {
        'case_id': str(case.get('case_id', 'unspecified')),
        'currency': 'EUR', 'principal': str(principal),
        'charges': charges, 'payments': payments,
        'charges_total': str(charges_total.quantize(CENT)),
        'payments_total': str(payments_total.quantize(CENT)),
        'reconstructed_total': str(reconstructed.quantize(CENT)),
        'claimed_total': str(claimed), 'difference': str(discrepancy.quantize(CENT)),
        'arithmetic_matches': discrepancy == 0,
        'needs_itemization': bool(not charges and claimed != principal - payments_total),
        'review_required': True,
        'disclaimer': 'Arithmetic check only. No conclusion on legality, limitation periods, notification validity or collectability.'
    }
