from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping


DEMO_ORDERS = [
    {"order_id": "o-1001", "customer_id": "c-001", "amount": 120.0, "status": "completed"},
    {"order_id": "o-1002", "customer_id": "c-001", "amount": 40.5, "status": "completed"},
    {"order_id": "o-1003", "customer_id": "c-002", "amount": 12.0, "status": "cancelled"},
    {"order_id": "o-1004", "customer_id": "c-002", "amount": 78.25, "status": "completed"},
    {"order_id": "o-1005", "customer_id": "c-003", "amount": 15.0, "status": "completed"},
]


@dataclass(frozen=True)
class OrderRecord:
    order_id: str
    customer_id: str
    amount: float
    status: str


def normalize_orders(rows: Iterable[Mapping[str, object]]) -> list[OrderRecord]:
    """Convert raw row mappings into validated order records."""
    normalized: list[OrderRecord] = []
    for row in rows:
        order_id = str(row.get("order_id", "")).strip()
        customer_id = str(row.get("customer_id", "")).strip()
        status = str(row.get("status", "")).strip().lower()
        amount_raw = row.get("amount", 0)

        if not order_id or not customer_id:
            continue

        try:
            amount = float(amount_raw)
        except (TypeError, ValueError):
            continue

        normalized.append(
            OrderRecord(
                order_id=order_id,
                customer_id=customer_id,
                amount=amount,
                status=status,
            )
        )

    return normalized


def aggregate_customer_orders(rows: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Aggregate completed orders into a customer-level summary."""
    totals: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "customer_id": "",
            "completed_order_count": 0,
            "completed_amount_total": 0.0,
        }
    )

    for order in normalize_orders(rows):
        if order.status != "completed":
            continue

        bucket = totals[order.customer_id]
        bucket["customer_id"] = order.customer_id
        bucket["completed_order_count"] = int(bucket["completed_order_count"]) + 1
        bucket["completed_amount_total"] = round(
            float(bucket["completed_amount_total"]) + order.amount,
            2,
        )

    summary = list(totals.values())
    summary.sort(key=lambda row: (-float(row["completed_amount_total"]), row["customer_id"]))
    return summary

