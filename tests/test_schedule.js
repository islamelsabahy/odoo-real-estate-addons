// Parity check: the browser calculator must match the Python schedule logic on the shared vectors.
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const S = require("../docs/schedule.js");

const vectors = JSON.parse(fs.readFileSync(path.join(__dirname, "web_vectors.json"), "utf8"));
let ok = 0, errs = 0;
for (const { input: i, expected } of vectors) {
  let got;
  try {
    got = { lines: S.build({ total: i.total, down: i.down, count: i.count, months: i.months, start: i.start, maint: i.maint, maintDue: i.maintDue }) };
  } catch (e) { got = { error: e.message }; }
  assert.deepStrictEqual(got, expected, JSON.stringify(i));
  if (got.error) errs++;
  else {
    assert.strictEqual(S.sumCents(got.lines), S.toCents(i.total), "lines must add up to the price " + JSON.stringify(i));
    ok++;
  }
}
assert.strictEqual(S.toCents("2.675"), 268n); // half-even on exact ties: 2.675 -> 2.68
assert.strictEqual(S.toCents("2.665"), 266n);
console.log(`ok - ${ok} schedules + ${errs} error cases match Python`);
