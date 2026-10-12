{
    "name": "Real Estate Installment Plans",
    "summary": "Down payment, installment schedule and maintenance deposit for unit sales",
    "description": """
Real Estate Installment Plans
=============================
Generates a payment schedule (down payment, N equal installments, optional
maintenance deposit) for a unit, tracks what is paid, and marks the unit as
sold when the plan is confirmed. Rounding differences are absorbed by the last
installment so the schedule always equals the unit price.
""",
    "version": "17.0.1.0.0",
    "category": "Real Estate",
    "author": "Islam El-Sherbiny",
    "license": "LGPL-3",
    "depends": ["re_unit", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/plan_views.xml",
    ],
    "installable": True,
}
