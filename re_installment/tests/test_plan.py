from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestReInstallmentPlan(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["re.project"].create({"name": "Plan Project", "code": "PP"})
        cls.unit = cls.env["re.unit"].create(
            {
                "name": "B-201",
                "project_id": cls.project.id,
                "area": 120.0,
                "price": 1_200_000.0,
            }
        )
        cls.buyer = cls.env["res.partner"].create({"name": "Plan Buyer"})

    def _plan(self, **overrides):
        vals = {
            "unit_id": self.unit.id,
            "partner_id": self.buyer.id,
            "total_price": 1_200_000.0,
            "down_payment_pct": 10.0,
            "installment_count": 8,
            "months_between": "3",
            "start_date": date(2026, 1, 1),
            "maintenance_pct": 8.0,
            "maintenance_due": date(2029, 1, 1),
        }
        vals.update(overrides)
        return self.env["re.installment.plan"].create(vals)

    def test_sequence_name(self):
        self.assertTrue(self._plan().name.startswith("PLAN/"))

    def test_generate_schedule(self):
        plan = self._plan()
        plan.action_generate()
        self.assertEqual(len(plan.line_ids), 10)  # down + 8 installments + maintenance
        self.assertAlmostEqual(plan.total_scheduled, 1_200_000.0, places=2)
        self.assertEqual(plan.line_ids[0].label, "Down payment")
        self.assertEqual(plan.line_ids[-1].label, "Maintenance deposit")
        self.assertAlmostEqual(plan.line_ids[0].amount, 120_000.0, places=2)

    def test_regenerate_replaces_lines(self):
        plan = self._plan()
        plan.action_generate()
        plan.installment_count = 4
        plan.action_generate()
        self.assertEqual(len(plan.line_ids), 6)

    def test_confirm_marks_unit_sold(self):
        plan = self._plan()
        plan.action_generate()
        plan.action_confirm()
        self.assertEqual(plan.state, "confirmed")
        self.assertEqual(self.unit.state, "sold")
        self.assertEqual(self.unit.buyer_id, self.buyer)

    def test_confirm_requires_schedule(self):
        with self.assertRaises(UserError):
            self._plan().action_confirm()

    def test_cannot_regenerate_after_confirm(self):
        plan = self._plan()
        plan.action_generate()
        plan.action_confirm()
        with self.assertRaises(UserError):
            plan.action_generate()

    def test_cancel_releases_unit(self):
        plan = self._plan()
        plan.action_generate()
        plan.action_confirm()
        plan.action_cancel()
        self.assertEqual(plan.state, "cancelled")
        self.assertEqual(self.unit.state, "available")
        self.assertFalse(self.unit.buyer_id)

    def test_cannot_cancel_with_paid_installment(self):
        plan = self._plan()
        plan.action_generate()
        plan.action_confirm()
        plan.line_ids[0].paid = True
        with self.assertRaises(UserError):
            plan.action_cancel()

    def test_balance_follows_payments(self):
        plan = self._plan()
        plan.action_generate()
        plan.line_ids[0].paid = True
        self.assertAlmostEqual(plan.total_paid, 120_000.0, places=2)
        self.assertAlmostEqual(plan.balance, 1_080_000.0, places=2)

    def test_terms_over_100_percent_rejected(self):
        with self.assertRaises(ValidationError):
            self._plan(down_payment_pct=60.0, maintenance_pct=40.0)

    def test_maintenance_needs_due_date(self):
        plan = self._plan(maintenance_due=False)
        with self.assertRaises(UserError):
            plan.action_generate()
