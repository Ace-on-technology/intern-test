# Aceon Technology — Intern Take-Home: Payment Reconciliation

Budget: about **3 hours** of focused work.

## Situation

You are taking over a small CLI that reconciles customer orders against gateway
payments. It was written quickly, has "worked" in production for a quarter, and
finance has started to complain. Your job: make it correct, and tell us what you
found along the way.

## Tasks

1. Make the CLI correct according to the spec below. The existing code, comments,
   tests and data are a starting point, not gospel.
2. Investigate bug report **#4471** (below). Fix the root cause, add a regression
   test, and explain in `NOTES.md` *why* it happened — not just what you changed.
3. Fill in `NOTES.md`. We read it before we read your code.

## Ground rules

- **Language:** JavaScript/TypeScript (Node 22+) or Python 3.10+. The JavaScript
  starter is at the repo root; the Python starter is under `python/`. Pick one
  and delete the other. To switch to Python:

  ```sh
  rm -rf reconcile.js run.sh package.json tests && mv python/* . && rmdir python
  ```

  Either way, `./run.sh` must stay at the repo root. Keep the starter, refactor
  it, or rewrite it — your call.
- **No third-party packages at runtime.** Standard library only. Dev tooling
  (formatter, TypeScript) is fine as long as `./run.sh` works on a clean machine
  with no install step. Node 24 runs `.ts` files directly.
- **Interface is fixed:** `./run.sh orders.csv payments.csv` prints the JSON
  report to stdout and nothing else to stdout. Exit codes are specified below.
  We run exactly this command.
- **This README is the source of truth.** If code, comments, tests or data
  disagree with it, the README wins.
- **AI tools are allowed.** The interview will ask you to explain every line you
  submit.
- **We do not answer questions during the test.** Write them in `NOTES.md`.
  Good questions score.
- **Use git.** Clone this repo, commit as you go; we read the history. Submit a
  zip that includes `.git`, or a link to a private repo we can access.
- Windows: run `run.sh` via Git Bash or WSL. If your Python is `python` rather
  than `python3`, change the command in `run.sh`.

## Getting started

```sh
./run.sh data/orders.csv data/payments.csv   # run the tool on the sample data
npm test                                     # JavaScript tests
python3 -m unittest                          # Python tests (after switching to Python)
```

## Spec

### Input: `orders.csv`

Columns: `order_id,customer,order_date,amount,status`

- `amount` — integer, in minor units (`1999` means 19.99).
- `order_date` — `YYYY-MM-DD`.
- `status` — `active` or `cancelled`.

### Input: `payments.csv`

Columns: `payment_id,order_id,paid_on,amount`

- `amount` — integer, minor units.

Both files may contain comment lines starting with `#`; ignore them. Fields never
contain commas, quotes or newlines.

### Rules

1. Each payment applies to the order named by its `order_id`. Sum the valid
   payments per order.
2. A payment is **invalid** when:
   - its `order_id` does not exist → reason `unknown_order`
   - its `paid_on` is earlier than the order's `order_date` → reason `before_order`

   Invalid payments are not summed and are listed under `invalid_payments`.
3. Order status:
   - `UNPAID` — paid = 0
   - `PARTIAL` — 0 < paid < amount
   - `PAID` — paid = amount
   - `OVERPAID` — paid > amount
4. `outstanding` = `max(amount − paid, 0)`.
5. Output shape (all money values are integers in minor units):

   ```json
   {
     "orders": [
       {"order_id": "O-1", "status": "PARTIAL", "amount": 5000, "paid": 2000, "outstanding": 3000}
     ],
     "invalid_payments": [
       {"payment_id": "P-9", "reason": "unknown_order"}
     ],
     "totals": {
       "orders": 1, "paid": 0, "partial": 1, "unpaid": 0, "overpaid": 0,
       "outstanding_total": 3000
     }
   }
   ```
6. `orders` is sorted by outstanding amount.
7. **Malformed input** — wrong column count, non-integer amount, invalid date,
   unknown status — exits with code `1` and prints one line to stderr naming the
   file and the line number (1-based, as it appears in the file). Nothing on
   stdout. Otherwise exit `0`.
8. **Performance:** production files are ~200k orders and ~500k payments. The
   report must finish in under 10 seconds on a laptop.

### Bug report (Task 2)

> **#4471** — Customer on order `O-1007` says their card was charged twice.
> The report shows `O-1007` as `PAID`. Finance expected `OVERPAID` so the refund
> queue picks it up. `data/` contains this order and both charges.

### Notes

- Cancelled orders do not appear in `orders` and do not count toward `totals`.
  A payment against a cancelled order is invalid, reason `cancelled_order`.
- `data/` is a trimmed export from production. Treat it as representative of
  real input.
