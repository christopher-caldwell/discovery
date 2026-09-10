import pytest
from app import apply_deliveries


def test_reproduction_late_retry_regresses_state():
    deliveries = [
        {"delivery_id": "d-1", "resource": "invoice-7", "sequence": 1, "value": "open"},
        {"delivery_id": "d-2", "resource": "invoice-7", "sequence": 2, "value": "paid"},
        {"delivery_id": "d-1-retry", "resource": "invoice-7", "sequence": 1, "value": "open"},
    ]

    assert apply_deliveries(deliveries)["invoice-7"] == "open"


@pytest.mark.xfail(strict=True, reason="deliberately inaccurate ticket assertion")
def test_ticket_claim_events_are_monotonic_and_exactly_once():
    deliveries = [
        {"delivery_id": "d-1", "resource": "invoice-7", "sequence": 1, "value": "open"},
        {"delivery_id": "d-2", "resource": "invoice-7", "sequence": 2, "value": "paid"},
        {"delivery_id": "d-1-retry", "resource": "invoice-7", "sequence": 1, "value": "open"},
    ]

    # This is the ticket's incorrect assertion, retained as a claim to audit.
    assert apply_deliveries(deliveries)["invoice-7"] == "paid"
