from databricks_pipeline.core import DEMO_ORDERS, aggregate_customer_orders, normalize_orders


def test_normalize_orders_skips_bad_rows():
    rows = [
        {"order_id": "a", "customer_id": "c1", "amount": "12.5", "status": "Completed"},
        {"order_id": "", "customer_id": "c1", "amount": "5", "status": "completed"},
        {"order_id": "b", "customer_id": "c2", "amount": "bad", "status": "completed"},
    ]

    normalized = normalize_orders(rows)

    assert len(normalized) == 1
    assert normalized[0].status == "completed"
    assert normalized[0].amount == 12.5


def test_aggregate_customer_orders_matches_demo_data():
    summary = aggregate_customer_orders(DEMO_ORDERS)

    assert summary == [
        {"customer_id": "c-001", "completed_order_count": 2, "completed_amount_total": 160.5},
        {"customer_id": "c-002", "completed_order_count": 1, "completed_amount_total": 78.25},
        {"customer_id": "c-003", "completed_order_count": 1, "completed_amount_total": 15.0},
    ]

