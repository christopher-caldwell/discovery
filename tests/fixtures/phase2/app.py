"""Deliberately small webhook consumer with an ordering/retry defect."""


def apply_deliveries(deliveries: list[dict[str, object]]) -> dict[str, object]:
    """Apply deliveries in arrival order and return the materialized state.

    The provider may retry a delivery. This consumer does not deduplicate or
    compare sequence numbers, so a late retry overwrites newer state.
    """
    state: dict[str, object] = {}
    for delivery in deliveries:
        state[str(delivery["resource"])] = delivery["value"]
    return state


if __name__ == "__main__":
    sample = [
        {"delivery_id": "d-1", "resource": "invoice-7", "sequence": 1, "value": "open"},
        {"delivery_id": "d-2", "resource": "invoice-7", "sequence": 2, "value": "paid"},
        {"delivery_id": "d-1-retry", "resource": "invoice-7", "sequence": 1, "value": "open"},
    ]
    print(apply_deliveries(sample))
