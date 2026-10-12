/* Browser port of re_installment/models/schedule.py (the Python code is the reference).
 * Money is BigInt cents and percentages are exact decimals, so results match Python's Decimal.
 * `node tests/test_schedule.js` replays tests/web_vectors.json (generated from Python) in CI.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.Schedule = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var DEC_RE = /^([+-]?)(\d+\.?\d*|\.\d+)(?:[eE]([+-]?\d+))?$/;

  /* exact decimal as {n: BigInt, k: scale}; value = n / 10^k */
  function dec(value) {
    var m = DEC_RE.exec(String(value).trim());
    if (!m) throw new Error("Not a number: " + value);
    var parts = m[2].split("."), frac = parts[1] || "";
    var n = BigInt((parts[0] || "0") + frac), k = frac.length - (m[3] ? parseInt(m[3], 10) : 0);
    if (k < 0) { n *= 10n ** BigInt(-k); k = 0; }
    return { n: m[1] === "-" ? -n : n, k: k };
  }
  function pow10(k) { return 10n ** BigInt(k); }

  /* Python: Decimal(str(x)).quantize(0.01), ROUND_HALF_EVEN -> cents */
  function toCents(value) {
    var d = dec(value);
    if (d.k <= 2) return d.n * pow10(2 - d.k);
    var div = pow10(d.k - 2), neg = d.n < 0n, a = neg ? -d.n : d.n;
    var q = a / div, r = a % div, twice = r * 2n;
    if (twice > div || (twice === div && q % 2n === 1n)) q += 1n;
    return neg ? -q : q;
  }
  /* floor(cents * pct / 100) for non-negative values (ROUND_DOWN) */
  function pctOf(cents, pct) { return (cents * pct.n) / (100n * pow10(pct.k)); }

  function fmtCents(c) {
    var neg = c < 0n, s = (neg ? -c : c).toString().padStart(3, "0");
    return (neg ? "-" : "") + s.slice(0, -2) + "." + s.slice(-2);
  }

  function parseDate(iso) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
    if (!m) throw new Error("Invalid date: " + iso);
    var y = +m[1], mo = +m[2], d = +m[3], t = new Date(Date.UTC(y, mo - 1, d));
    if (t.getUTCFullYear() !== y || t.getUTCMonth() !== mo - 1 || t.getUTCDate() !== d) throw new Error("Invalid date: " + iso);
    return { y: y, m: mo, d: d };
  }
  function pad(n, w) { return String(n).padStart(w, "0"); }
  function iso(dt) { return pad(dt.y, 4) + "-" + pad(dt.m, 2) + "-" + pad(dt.d, 2); }
  function daysIn(y, m) { return new Date(Date.UTC(y, m, 0)).getUTCDate(); }

  /* Add calendar months, clamping the day (Jan 31 + 1 month = Feb 28/29). */
  function addMonths(dt, months) {
    var idx = dt.m - 1 + months, y = dt.y + Math.floor(idx / 12), m = ((idx % 12) + 12) % 12 + 1;
    return { y: y, m: m, d: Math.min(dt.d, daysIn(y, m)) };
  }

  /* Same rules and messages as build_schedule(); amounts are strings with 2 decimals. */
  function build(opts) {
    var total = toCents(opts.total);
    if (total <= 0n) throw new Error("Total price must be positive.");
    var count = opts.count, months = opts.months;
    if (!(count >= 1)) throw new Error("At least one installment is required.");
    if (!(months >= 1)) throw new Error("Months between installments must be at least 1.");
    var down = dec(opts.down === "" || opts.down == null ? "0" : opts.down);
    var maint = dec(opts.maint === "" || opts.maint == null ? "0" : opts.maint);
    if (down.n < 0n || maint.n < 0n) throw new Error("Percentages cannot be negative.");
    // down + maint >= 100  <=>  compare on a common scale
    var k = Math.max(down.k, maint.k);
    var sum = down.n * pow10(k - down.k) + maint.n * pow10(k - maint.k);
    if (sum >= 100n * pow10(k)) throw new Error("Down payment plus maintenance must be below 100%.");
    if (maint.n > 0n && !opts.maintDue) throw new Error("A maintenance due date is required when maintenance % is set.");

    var start = parseDate(opts.start);
    var downC = pctOf(total, down), maintC = pctOf(total, maint);
    var remaining = total - downC - maintC;
    var n = BigInt(count), base = remaining / n, last = remaining - base * (n - 1n);
    var lines = [];
    if (downC > 0n) lines.push({ label: "Down payment", due_date: iso(start), amount: fmtCents(downC) });
    for (var i = 1; i <= count; i++)
      lines.push({ label: "Installment " + i + "/" + count, due_date: iso(addMonths(start, i * months)),
        amount: fmtCents(i === count ? last : base) });
    if (maintC > 0n) lines.push({ label: "Maintenance deposit", due_date: iso(parseDate(opts.maintDue)), amount: fmtCents(maintC) });
    return lines;
  }

  function sumCents(lines) { return lines.reduce(function (a, l) { return a + toCents(l.amount); }, 0n); }

  return { build: build, addMonths: addMonths, toCents: toCents, fmtCents: fmtCents, sumCents: sumCents };
});
