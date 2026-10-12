from odoo import fields, models


class ReProject(models.Model):
    _name = "re.project"
    _description = "Real Estate Project"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, copy=False)
    location = fields.Char()
    unit_ids = fields.One2many("re.unit", "project_id", string="Units")
    unit_count = fields.Integer(compute="_compute_unit_count")

    _sql_constraints = [
        ("code_unique", "unique(code)", "Project code must be unique."),
    ]

    def _compute_unit_count(self):
        for project in self:
            project.unit_count = len(project.unit_ids)
