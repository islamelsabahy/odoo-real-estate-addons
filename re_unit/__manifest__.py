{
    "name": "Real Estate Units",
    "summary": "Projects and sellable units with availability status",
    "description": """
Real Estate Units
=================
Foundation module for real estate developers: projects, units (apartment, villa,
office, retail), pricing, and a simple Available / Reserved / Sold workflow.
""",
    "version": "17.0.1.0.0",
    "category": "Real Estate",
    "author": "Islam El-Sherbiny",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/unit_views.xml",
    ],
    "application": True,
    "installable": True,
}
