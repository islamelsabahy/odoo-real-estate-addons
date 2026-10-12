# odoo-real-estate-addons

[![CI](https://github.com/islamelsabahy/odoo-real-estate-addons/actions/workflows/ci.yml/badge.svg)](https://github.com/islamelsabahy/odoo-real-estate-addons/actions/workflows/ci.yml)

**EN** — Odoo 17 add-ons for real estate developers: a units catalog with availability status, and installment plans (down payment, equal installments, maintenance deposit) that mark the unit as sold on confirmation.

**AR** — موديولات Odoo 17 لشركات التطوير العقاري: كتالوج الوحدات بحالة الإتاحة، وخطط التقسيط (مقدم، أقساط متساوية، وديعة صيانة) مع تحويل الوحدة لـ "مباعة" عند التأكيد.

## Modules / الموديولات

| Module | Depends on | What it gives you | الوصف |
|---|---|---|---|
| `re_unit` | `base` | Projects, units (apartment/villa/office/retail), price per m², Available → Reserved → Sold | المشاريع والوحدات وحالة الإتاحة |
| `re_installment` | `re_unit`, `mail` | Installment plan with generated schedule, paid tracking, balance, chatter | خطة التقسيط وجدول الدفعات ومتابعة المدفوع |

## How the schedule works / منطق الجدول

- Down payment is due on the plan start date (% of price).
- Installments split what remains after down payment and maintenance. Installment *k* is due *k × months* after the start date, calculated from the start date each time, so month-end dates do not drift.
- The maintenance deposit is a separate line with its own due date.
- Rounding differences go to the last installment, so the schedule always equals the unit price.

The logic lives in `re_installment/models/schedule.py` with no Odoo imports, so it is unit-tested without an Odoo install:

```bash
python -m unittest discover -s tests -v
```

## Install / التثبيت

1. Copy `re_unit` and `re_installment` into your Odoo addons path.
2. Restart Odoo, enable developer mode, then Apps → Update Apps List.
3. Install **Real Estate Installment Plans** (it pulls in `re_unit`).

## Try it locally / تجربة محلية

A staging setup with Odoo 17 and PostgreSQL is included. The database is not exposed outside the Docker network, and Odoo listens on localhost only.

```bash
cp .env.example .env          # set your own POSTGRES_PASSWORD
docker compose up -d          # then open http://localhost:8069 and create a database
./scripts/run_odoo_tests.sh   # installs both modules in a throwaway DB and runs their tests
```

## Tests / الاختبارات

| Layer | Where it runs | Covers |
|---|---|---|
| Schedule logic (`tests/`) | Anywhere, no Odoo | Rounding, month-end dates, validation |
| Odoo tests (`re_unit/tests`, `re_installment/tests`) | Odoo 17 (CI uses the official image) | Unit workflow, constraints, plan generate/confirm/cancel, balances |

## Status and limits / الحالة

- The pure schedule logic is unit-tested. The Odoo models and views were written for Odoo 17 but **have not been run on a live Odoo instance yet**: test on a staging database first.
- Access rights give all internal users read/write/create. Tighten with dedicated groups before production.
- Not included yet: payment registration against invoices/journal entries, cheque tracking, sales commissions, Odoo 18 `<list>` views.

## Roadmap

- [ ] Link plan lines to customer invoices and payments
- [ ] Cheque register (post-dated cheques per installment)
- [ ] Sales agent commission rules
- [ ] Odoo 18 branch
- [ ] Arabic translation (`i18n/ar.po`)

## License

LGPL-3
