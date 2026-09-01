import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { classify, reconcile } from "../reconcile.js";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const order = (orderId, orderDate, amount, status = "active") => ({
  orderId, customer: "test", orderDate, amount, status,
});
const payment = (paymentId, orderId, paidOn, amount) => ({ paymentId, orderId, paidOn, amount });

test("classify: nothing paid is UNPAID", () => {
  assert.equal(classify(100, 0), "UNPAID");
});

test("classify: something paid is PARTIAL", () => {
  assert.equal(classify(100, 40), "PARTIAL");
});

test("classify: full amount is PAID", () => {
  assert.equal(classify(100, 100), "PAID");
});

test("reconcile: two payments summing to the amount", () => {
  // Two partial payments stay PARTIAL until the nightly settlement job marks
  // the order settled, so reconcile must not report PAID here.
  const report = reconcile(
    [order("O-1", "2026-03-01", 5000)],
    [payment("P-1", "O-1", "2026-03-02", 2500), payment("P-2", "O-1", "2026-03-03", 2500)],
  );
  assert.equal(report.orders[0].status, "PARTIAL");
});

test("reconcile: payment before the order date is invalid", () => {
  const report = reconcile(
    [order("O-1", "2026-03-10", 1000)],
    [payment("P-1", "O-1", "2026-03-09", 1000)],
  );
  assert.equal(report.orders[0].status, "UNPAID");
  assert.deepEqual(report.invalid_payments, [{ payment_id: "P-1", reason: "before_order" }]);
});

test("reconcile: payment for an unknown order is invalid", () => {
  const report = reconcile(
    [order("O-1", "2026-03-01", 1000)],
    [payment("P-1", "O-404", "2026-03-02", 1000)],
  );
  assert.deepEqual(report.invalid_payments, [{ payment_id: "P-1", reason: "unknown_order" }]);
});

test("reconcile: totals count each status", () => {
  const report = reconcile(
    [order("O-1", "2026-03-01", 1000), order("O-2", "2026-03-01", 1000), order("O-3", "2026-03-01", 1000)],
    [payment("P-1", "O-1", "2026-03-02", 1000), payment("P-2", "O-2", "2026-03-02", 300)],
  );
  assert.equal(report.totals.orders, 3);
  assert.equal(report.totals.paid, 1);
  assert.equal(report.totals.partial, 1);
  assert.equal(report.totals.unpaid, 1);
});

test("cli: runs on the sample data", () => {
  const result = spawnSync("bash", ["run.sh", "data/orders.csv", "data/payments.csv"], {
    cwd: ROOT, encoding: "utf8",
  });
  assert.equal(result.status, 0, result.stderr);
  JSON.parse(result.stdout);
});
