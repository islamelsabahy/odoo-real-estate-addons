from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .schedule import build_schedule


class ReInstallmentPlan(models.Model):
    _name = "re.installment.plan"
    _description = "Installment Plan"
    _inherit = ["mail.thread"]
    _order = "id desc"

    name = fields.Char(default="New", copy=False, readonly=True)
    unit_id = fields.Many2one(
        "re.unit",
        required=True,
        domain="[('state', 'in', ('available', 'reserved'))]",
        tracking=True,
    )
    partner_id = fields.Many2one("res.partner", string="Buyer", required=True, tracking=True)
    currency_id = fields.Many2one(related="unit_id.currency_id")
    total_price = fields.Monetary(required=True, currency_field="currency_id")
    down_payment_pct = fields.Float("Down payment %", default=10.0)
    installment_count = fields.Integer(default=8)
    months_between = fields.Selection(
        [("1", "Monthly"), ("3", "Quarterly"), ("6", "Semi-annual"), ("12", "Annual")],
        default="3",
        required=True,
    )
    start_date = fields.Date(default=fields.Date.context_today, required=True)
    maintenance_pct = fields.Float("Maintenance deposit %", default=0.0)
    maintenance_due = fields.Date("Maintenance due date")
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled")],
        default="draft",
        tracking=True,
    )
    line_ids = fields.One2many("re.installment.line", "plan_id", string="Schedule")
    total_scheduled = fields.Monetary(compute="_compute_totals", currency_field="currency_id")
    total_paid = fields.Monetary(compute="_compute_totals", currency_field="currency_id")
    balance = fields.Monetary(compute="_compute_totals", currency_field="currency_id")

    @api.depends("line_ids.amount", "line_ids.paid")
    def _compute_totals(self):
        for plan in self:
            plan.total_scheduled = sum(plan.line_ids.mapped("amount"))
            plan.total_paid = sum(plan.line_ids.filtered("paid").mapped("amount"))
            plan.balance = plan.total_scheduled - plan.total_paid

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("re.installment.plan") or "New"
        return super().create(vals_list)

    @api.onchange("unit_id")
    def _onchange_unit_id(self):
        if self.unit_id and self.unit_id.price:
            self.total_price = self.unit_id.price

    @api.constrains("installment_count", "down_payment_pct", "maintenance_pct")
    def _check_terms(self):
        for plan in self:
            if plan.installment_count < 1:
                raise ValidationError("At least one installment is required.")
            if plan.down_payment_pct + plan.maintenance_pct >= 100:
                raise ValidationError("Down payment plus maintenance must be below 100%.")

    def action_generate(self):
        for plan in self:
            if plan.state != "draft":
                raise UserError("Schedule can only be regenerated while the plan is in draft.")
            try:
                lines = build_schedule(
                    plan.total_price,
                    plan.down_payment_pct,
                    plan.installment_count,
                    int(plan.months_between),
                    plan.start_date,
                    plan.maintenance_pct,
                    plan.maintenance_due or None,
                )
            except ValueError as exc:
                raise UserError(str(exc)) from exc
            plan.line_ids.unlink()
            self.env["re.installment.line"].create(
                [
                    {
                        "plan_id": plan.id,
                        "sequence": index,
                        "label": line["label"],
                        "due_date": line["due_date"],
                        "amount": float(line["amount"]),
                    }
                    for index, line in enumerate(lines, start=1)
                ]
            )

    def action_confirm(self):
        for plan in self:
            if not plan.line_ids:
                raise UserError("Generate the schedule before confirming.")
            if abs(plan.total_scheduled - plan.total_price) > 0.005:
                raise UserError("The schedule total does not match the unit price.")
            if plan.unit_id.state == "sold":
                raise UserError(f"Unit {plan.unit_id.name} is already sold.")
            plan.unit_id.write({"state": "sold", "buyer_id": plan.partner_id.id})
            plan.state = "confirmed"

    def action_cancel(self):
        for plan in self:
            if plan.state == "confirmed" and any(plan.line_ids.filtered("paid")):
                raise UserError("Cannot cancel a plan that already has paid installments.")
            if plan.state == "confirmed":
                plan.unit_id.write({"state": "available", "buyer_id": False})
            plan.state = "cancelled"

    def action_reset_draft(self):
        self.filtered(lambda p: p.state == "cancelled").write({"state": "draft"})


class ReInstallmentLine(models.Model):
    _name = "re.installment.line"
    _description = "Installment Line"
    _order = "plan_id, sequence"

    plan_id = fields.Many2one("re.installment.plan", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    label = fields.Char(required=True)
    due_date = fields.Date(required=True)
    currency_id = fields.Many2one(related="plan_id.currency_id")
    amount = fields.Monetary(currency_field="currency_id")
    paid = fields.Boolean()
    paid_date = fields.Date()
