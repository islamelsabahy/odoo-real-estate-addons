"""Generate tests/web_vectors.json: schedule inputs plus what the Python reference returns.

    python scripts/build_web_data.py          # write
    python scripts/build_web_data.py --check  # exit 1 if stale (used by the tests)

docs/schedule.js (the browser calculator) must reproduce every vector exactly.
"""
import importlib.util
import json
import os
import random
import sys
from datetime import date

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
_spec = importlib.util.spec_from_file_location("schedule", os.path.join(ROOT, "re_installment", "models", "schedule.py"))
schedule = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(schedule)

TARGET = os.path.join(ROOT, "tests", "web_vectors.json")

CASES = [
    # total, down %, count, months, start, maint %, maint due
    ("1200000", "10", 12, 3, "2026-01-31", "0", None),
    ("2500000", "15", 24, 3, "2026-02-15", "2", "2028-02-15"),
    ("1000000", "20", 7, 1, "2026-03-31", "0", None),
    ("999999.99", "12.5", 5, 6, "2026-01-01", "0", None),
    ("1000000", "0", 10, 1, "2026-01-29", "0", None),
    ("100", "33.333", 3, 1, "2026-01-01", "0", None),
    ("0.05", "0", 3, 1, "2026-01-01", "0", None),
    ("2400000", "10", 1, 12, "2024-02-29", "0", None),
    ("3000000", "5", 60, 1, "2026-12-31", "1.5", "2027-06-30"),
    ("1234567.891", "7.77", 11, 2, "2026-05-10", "0", None),
    ("500000", "0", 4, 12, "2028-02-29", "0", None),
    # errors
    ("0", "10", 12, 3, "2026-01-01", "0", None),
    ("-5", "10", 12, 3, "2026-01-01", "0", None),
    ("1000", "10", 0, 3, "2026-01-01", "0", None),
    ("1000", "10", 12, 0, "2026-01-01", "0", None),
    ("1000", "-1", 12, 3, "2026-01-01", "0", None),
    ("1000", "60", 12, 3, "2026-01-01", "40", "2027-01-01"),
    ("1000", "100", 12, 3, "2026-01-01", "0", None),
    ("1000", "10", 12, 3, "2026-01-01", "5", None),
]


def _run(case):
    total, down, n, m, start, mp, md = case
    try:
        lines = schedule.build_schedule(total, down, n, m, date.fromisoformat(start), mp,
                                        date.fromisoformat(md) if md else None)
    except ValueError as exc:
        return {"error": str(exc)}
    return {"lines": [{"label": l["label"], "due_date": l["due_date"].isoformat(), "amount": str(l["amount"])}
                      for l in lines]}


def _cases():
    out = list(CASES)
    rnd = random.Random(2026)
    for _ in range(120):
        total = f"{rnd.randint(1, 9_000_000)}.{rnd.randint(0, 999):03d}"[: rnd.choice([7, 9, 11])]
        down = rnd.choice(["0", "5", "10", "12.5", "20", "33.333", "7.77", "0.1"])
        mp = rnd.choice(["0", "0", "1", "2.5"])
        start = date(rnd.randint(2024, 2030), rnd.randint(1, 12), rnd.randint(1, 28))
        if rnd.random() < .4:  # month-end starts exercise the day clamping
            start = date(start.year, rnd.choice([1, 3, 5, 7, 8, 10, 12]), 31)
        md = date(start.year + 2, start.month, 1).isoformat() if mp != "0" else None
        out.append((total, down, rnd.randint(1, 48), rnd.choice([1, 2, 3, 4, 6, 12]), start.isoformat(), mp, md))
    return out


def vectors_json():
    items = []
    for c in _cases():
        items.append({"input": {"total": c[0], "down": c[1], "count": c[2], "months": c[3], "start": c[4],
                                "maint": c[5], "maintDue": c[6]}, "expected": _run(c)})
    return json.dumps(items, indent=1) + "\n"


def stale():
    try:
        with open(TARGET, encoding="utf-8") as fh:
            cur = fh.read()
    except OSError:
        cur = None
    return [] if cur == vectors_json() else [os.path.relpath(TARGET, ROOT)]


if __name__ == "__main__":
    if "--check" in sys.argv:
        s = stale()
        if s:
            print("stale: " + ", ".join(s) + " (run python scripts/build_web_data.py)")
            sys.exit(1)
        print("web data is up to date")
    else:
        with open(TARGET, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(vectors_json())
        print("wrote", os.path.relpath(TARGET, ROOT))
