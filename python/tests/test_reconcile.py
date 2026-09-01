import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import reconcile as r  # noqa: E402


def order(order_id, order_date, amount, status="active"):
    return {"order_id": order_id, "customer": "test", "order_date": order_date,
            "amount": amount, "status": status}


def payment(payment_id, order_id, paid_on, amount):
    return {"payment_id": payment_id, "order_id": order_id, "paid_on": paid_on, "amount": amount}


class ClassifyTests(unittest.TestCase):
    def test_nothing_paid_is_unpaid(self):
        self.assertEqual(r.classify(100, 0), "UNPAID")

    def test_something_paid_is_partial(self):
        self.assertEqual(r.classify(100, 40), "PARTIAL")

    def test_full_amount_is_paid(self):
        self.assertEqual(r.classify(100, 100), "PAID")


class ReconcileTests(unittest.TestCase):
    def test_two_payments_summing_to_the_amount(self):
        # Two partial payments stay PARTIAL until the nightly settlement job
        # marks the order settled, so reconcile must not report PAID here.
        report = r.reconcile(
            [order("O-1", "2026-03-01", 5000)],
            [payment("P-1", "O-1", "2026-03-02", 2500), payment("P-2", "O-1", "2026-03-03", 2500)],
        )
        self.assertEqual(report["orders"][0]["status"], "PARTIAL")

    def test_payment_before_order_date_is_invalid(self):
        report = r.reconcile(
            [order("O-1", "2026-03-10", 1000)],
            [payment("P-1", "O-1", "2026-03-09", 1000)],
        )
        self.assertEqual(report["orders"][0]["status"], "UNPAID")
        self.assertEqual(report["invalid_payments"], [{"payment_id": "P-1", "reason": "before_order"}])

    def test_payment_for_unknown_order_is_invalid(self):
        report = r.reconcile(
            [order("O-1", "2026-03-01", 1000)],
            [payment("P-1", "O-404", "2026-03-02", 1000)],
        )
        self.assertEqual(report["invalid_payments"], [{"payment_id": "P-1", "reason": "unknown_order"}])

    def test_totals_count_each_status(self):
        report = r.reconcile(
            [order("O-1", "2026-03-01", 1000), order("O-2", "2026-03-01", 1000), order("O-3", "2026-03-01", 1000)],
            [payment("P-1", "O-1", "2026-03-02", 1000), payment("P-2", "O-2", "2026-03-02", 300)],
        )
        self.assertEqual(report["totals"]["orders"], 3)
        self.assertEqual(report["totals"]["paid"], 1)
        self.assertEqual(report["totals"]["partial"], 1)
        self.assertEqual(report["totals"]["unpaid"], 1)


class CliTests(unittest.TestCase):
    def test_runs_on_the_sample_data(self):
        result = subprocess.run(
            ["bash", "run.sh", "data/orders.csv", "data/payments.csv"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        json.loads(result.stdout)


if __name__ == "__main__":
    unittest.main()
