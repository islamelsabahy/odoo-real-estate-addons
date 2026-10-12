from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ReUnit(models.Model):
    _name = "re.unit"
    _description = "Real Estate Unit"
    _order = "project_id, name"

    name = fields.Char("Unit No.", required=True)
    project_id = fields.Many2one("re.project", required=True, ondelete="restrict")
    unit_type = fields.Selection(
        [
            ("apartment", "Apartment"),
            ("villa", "Villa"),
            ("office", "Office"),
            ("retail", "Retail"),
        ],
        default="apartment",
        required=True,
    )
    floor = fields.Integer()
    area = fields.Float("Area (m²)")
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id
    )
    price = fields.Monetary(currency_field="currency_id")
    price_per_m2 = fields.Monetary(compute="_compute_price_per_m2", currency_field="currency_id")
    state = fields.Selection(
        [("available", "Available"), ("reserved", "Reserved"), ("sold", "Sold")],
        default="available",
        required=True,
        copy=False,
    )
    buyer_id = fields.Many2one("res.partner", string="Buyer", copy=False)

    _sql_constraints = [
        ("unit_unique", "unique(project_id, name)", "This unit number already exists in the project."),
    ]

    @api.depends("price", "area")
    def _compute_price_per_m2(self):
        for unit in self:
            unit.price_per_m2 = unit.price / unit.area if unit.area else 0.0

    @api.constrains("price", "area")
    def _check_positive(self):
        for unit in self:
            if unit.price < 0 or unit.area < 0:
                raise ValidationError("Price and area cannot be negative.")

    def action_reserve(self):
        for unit in self:
            if unit.state != "available":
                raise UserError(f"Unit {unit.name} is not available.")
            unit.state = "reserved"

    def action_mark_sold(self):
        for unit in self:
            if unit.state == "sold":
                raise UserError(f"Unit {unit.name} is already sold.")
            unit.state = "sold"

    def action_release(self):
        for unit in self:
            unit.write({"state": "available", "buyer_id": False})
