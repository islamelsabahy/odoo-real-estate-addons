#!/usr/bin/env bash
# Install both modules in a throwaway database and run their Odoo tests.
# Usage: cp .env.example .env && ./scripts/run_odoo_tests.sh
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose up -d db
docker compose run --rm odoo \
  odoo -d "test_$(date +%s)" -i re_unit,re_installment \
  --test-enable --stop-after-init --log-level=test 2>&1 | tee /tmp/odoo-test.log

if grep -E " 0 failed, 0 error\(s\) of [1-9][0-9]* tests" /tmp/odoo-test.log; then
  echo "PASS: Odoo module tests"
else
  echo "FAIL: see /tmp/odoo-test.log" >&2
  exit 1
fi
