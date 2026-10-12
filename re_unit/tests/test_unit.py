from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestReUnit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["re.project"].create({"name": "Test Project", "code": "TP"})
        cls.unit = cls.env["re.unit"].create(
            {
                "name": "A-101",
                "project_id": cls.project.id,
                "area": 100.0,
                "price": 2_000_000.0,
            }
        )
        cls.buyer = cls.env["res.partner"].create({"name": "Test Buyer"})

    def test_price_per_m2(self):
        self.assertAlmostEqual(self.unit.price_per_m2, 20_000.0, places=2)

    def test_price_per_m2_without_area(self):
        unit = self.unit.copy({"name": "A-102", "area": 0.0})
        self.assertEqual(unit.price_per_m2, 0.0)

    def test_new_unit_is_available(self):
        self.assertEqual(self.unit.state, "available")

    def test_reserve_flow(self):
        self.unit.action_reserve()
        self.assertEqual(self.unit.state, "reserved")
        with self.assertRaises(UserError):
            self.unit.action_reserve()

    def test_mark_sold_twice_fails(self):
        self.unit.action_mark_sold()
        self.assertEqual(self.unit.state, "sold")
        with self.assertRaises(UserError):
            self.unit.action_mark_sold()

    def test_release_clears_buyer(self):
        self.unit.write({"state": "sold", "buyer_id": self.buyer.id})
        self.unit.action_release()
        self.assertEqual(self.unit.state, "available")
        self.assertFalse(self.unit.buyer_id)

    def test_copy_does_not_carry_state_or_buyer(self):
        self.unit.write({"state": "sold", "buyer_id": self.buyer.id})
        clone = self.unit.copy({"name": "A-103"})
        self.assertEqual(clone.state, "available")
        self.assertFalse(clone.buyer_id)

    def test_negative_price_rejected(self):
        with self.assertRaises(ValidationError):
            self.unit.price = -1.0

    def test_unit_number_unique_per_project(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.env["re.unit"].create({"name": "A-101", "project_id": self.project.id})

    def test_project_code_unique(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.env["re.project"].create({"name": "Other", "code": "TP"})

    def test_project_unit_count(self):
        self.assertEqual(self.project.unit_count, 1)
