"""Pure payment-schedule logic. No Odoo imports, so it can be unit-tested anywhere."""

import calendar
from datetime import date
from decimal import ROUND_DOWN, Decimal
from typing import Dict, List, Optional

CENT = Decimal("0.01")


def add_months(start: date, months: int) -> date:
    """Add calendar months, clamping the day (Jan 31 + 1 month = Feb 28/29)."""
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT)


def build_schedule(
    total_price,
    down_payment_pct,
    installment_count: int,
    months_between: int,
    start_date: date,
    maintenance_pct=0,
    maintenance_due: Optional[date] = None,
) -> List[Dict]:
    """Return schedule lines as dicts: label, due_date, amount (Decimal).

    * Down payment is due on ``start_date``.
    * Installment k is due ``k * months_between`` months after ``start_date``
      (computed from the start date each time, so month-end dates do not drift).
    * Maintenance deposit, if any, is a separate line due on ``maintenance_due``.
    * Installments split what remains after down payment and maintenance; the
      last installment absorbs rounding so the lines always add up to the price.
    """
    total = _money(total_price)
    if total <= 0:
        raise ValueError("Total price must be positive.")
    if installment_count < 1:
        raise ValueError("At least one installment is required.")
    if months_between < 1:
        raise ValueError("Months between installments must be at least 1.")
    down_pct = Decimal(str(down_payment_pct))
    maint_pct = Decimal(str(maintenance_pct))
    if down_pct < 0 or maint_pct < 0:
        raise ValueError("Percentages cannot be negative.")
    if down_pct + maint_pct >= 100:
        raise ValueError("Down payment plus maintenance must be below 100%.")
    if maint_pct > 0 and maintenance_due is None:
        raise ValueError("A maintenance due date is required when maintenance % is set.")

    down = (total * down_pct / 100).quantize(CENT, rounding=ROUND_DOWN)
    maintenance = (total * maint_pct / 100).quantize(CENT, rounding=ROUND_DOWN)
    remaining = total - down - maintenance
    base = (remaining / installment_count).quantize(CENT, rounding=ROUND_DOWN)
    last = remaining - base * (installment_count - 1)

    lines: List[Dict] = []
    if down > 0:
        lines.append({"label": "Down payment", "due_date": start_date, "amount": down})
    for k in range(1, installment_count + 1):
        lines.append(
            {
                "label": f"Installment {k}/{installment_count}",
                "due_date": add_months(start_date, k * months_between),
                "amount": last if k == installment_count else base,
            }
        )
    if maintenance > 0:
        lines.append({"label": "Maintenance deposit", "due_date": maintenance_due, "amount": maintenance})
    return lines
