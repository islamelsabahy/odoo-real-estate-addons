"""Standalone tests for the pure schedule logic (no Odoo needed).

Run from the repository root:  python -m unittest discover -s tests -v
"""

import importlib.util
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / "re_installment" / "models" / "schedule.py"
_spec = importlib.util.spec_from_file_location("schedule", _path)
schedule = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(schedule)


class AddMonthsTests(unittest.TestCase):
    def test_month_end_clamps(self):
        self.assertEqual(schedule.add_months(date(2026, 1, 31), 1), date(2026, 2, 28))
        self.assertEqual(schedule.add_months(date(2028, 1, 31), 1), date(2028, 2, 29))

    def test_year_rollover(self):
        self.assertEqual(schedule.add_months(date(2026, 11, 15), 3), date(2027, 2, 15))


class BuildScheduleTests(unittest.TestCase):
    def test_lines_sum_to_total(self):
        lines = schedule.build_schedule(1_000_000, 10, 7, 3, date(2026, 1, 1), 5, date(2028, 6, 1))
        self.assertEqual(sum(l["amount"] for l in lines), Decimal("1000000.00"))

    def test_rounding_absorbed_by_last_installment(self):
        lines = schedule.build_schedule(100, 0, 3, 1, date(2026, 1, 1))
        self.assertEqual([l["amount"] for l in lines], [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")])

    def test_structure(self):
        lines = schedule.build_schedule(1_200_000, 10, 8, 3, date(2026, 1, 1), 8, date(2029, 1, 1))
        self.assertEqual(len(lines), 10)  # down + 8 installments + maintenance
        self.assertEqual(lines[0]["label"], "Down payment")
        self.assertEqual(lines[0]["amount"], Decimal("120000.00"))
        self.assertEqual(lines[-1]["label"], "Maintenance deposit")
        self.assertEqual(lines[-1]["amount"], Decimal("96000.00"))
        self.assertEqual(lines[1]["due_date"], date(2026, 4, 1))

    def test_no_day_drift(self):
        lines = schedule.build_schedule(1000, 0, 3, 1, date(2026, 1, 31))
        self.assertEqual(
            [l["due_date"] for l in lines],
            [date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30)],
        )

    def test_zero_down_payment_has_no_down_line(self):
        lines = schedule.build_schedule(1000, 0, 2, 1, date(2026, 1, 1))
        self.assertEqual(len(lines), 2)

    def test_invalid_inputs(self):
        start = date(2026, 1, 1)
        with self.assertRaises(ValueError):
            schedule.build_schedule(0, 10, 4, 3, start)
        with self.assertRaises(ValueError):
            schedule.build_schedule(1000, 10, 0, 3, start)
        with self.assertRaises(ValueError):
            schedule.build_schedule(1000, 60, 4, 3, start, 40, start)
        with self.assertRaises(ValueError):
            schedule.build_schedule(1000, 10, 4, 3, start, 5, None)
        with self.assertRaises(ValueError):
            schedule.build_schedule(1000, 10, 4, 0, start)


if __name__ == "__main__":
    unittest.main()
