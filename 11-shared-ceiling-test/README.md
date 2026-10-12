# Shared ceiling test: 40 concurrent payments across 3 agents, one $6,000 company limit

`shared_ceiling_test.py` checks whether the **Pink Agentic AI Payments** sandbox enforces a
**shared company daily ceiling** correctly when several different agents fire payment requests
at the same time, not just when one agent requests payments alone.

It creates a disposable sandbox workspace (`coffee` template), reads each of 3 agents' own
budget, plans payment amounts so that only the shared ceiling (not any agent's own monthly
budget or per-payment cap) can block a request, then fires 40 of those requests **concurrently**
from all 3 agents at once, and checks the server's own running total afterward.

**Sandbox only: test credentials, no money moves, production not available.**

## What it does

1. `POST /v1/sandbox/workspaces` creates a fresh `coffee`-template workspace. That template seeds
   4 agents sharing one `company_daily_ceiling`; this script uses 3 of them (`a_purch`, `a_inv`,
   `a_pay` - the 4th, `a_mkt`, is skipped because its only allow-rule needs an ads-category payee
   this template does not seed, which would add unrelated `ask` decisions).
2. `GET /v1/budget` for each agent to read its own `left_this_month`, `single_payment_cap`, the
   shared `company_daily_ceiling`, and `company_spent_today`.
3. Plans 40 requests across the 3 agents so the combined requested total is noticeably above the
   ceiling, while each agent's own share stays far under its own monthly budget and per-payment
   cap - so the only rule that can possibly block a request is the shared ceiling.
4. Fires all 40 `POST /v1/payments` requests at once (one thread pool, no artificial delay).
5. Prints a summary (allowed/blocked counts and sums, block reasons) and reconciles the
   client-side allowed sum against the server's own `GET /v1/budget` -> `company_spent_today`.

## How to run

```bash
pip install requests
python3 shared_ceiling_test.py
```

No API key to set up: the script creates its own sandbox workspace each run and never prints a
raw agent key (only a masked `pk_sandbox_a...XXXX` excerpt).

## Real output, 2026-10-12

```
== Creating sandbox workspace (template=coffee) ==
Workspace: eikcbpnf79
  a_purch: pk_sandbox_a...a7b9
  a_inv: pk_sandbox_a...f000
  a_pay: pk_sandbox_a...e9ab

== Reading each agent's budget (GET /v1/budget) ==
  a_purch: left_this_month=1740 single_payment_cap=500
  a_inv: left_this_month=1320 single_payment_cap=300
  a_pay: left_this_month=17210 single_payment_cap=15000
  company_daily_ceiling=6000 company_spent_today=0

== Plan: 40 requests across 3 agents, requested_sum=$7940 vs ceiling=$6000 ==
  a_purch: 4 x $100 = $400
  a_inv: 2 x $200 = $400
  a_pay: 34 x $210 = $7140

== Firing 40 requests concurrently ==

== Summary ==
{
  "workspace_id": "eikcbpnf79",
  "n_requests": 40,
  "requested_sum": 7940,
  "allowed_count": 30,
  "allowed_sum": 5840,
  "blocked_count": 10,
  "blocked_by_rule": {
    "Company daily ceiling reached": 10
  },
  "other_count": 0,
  "company_daily_ceiling": 6000,
  "company_spent_today_before": 0
}

== Reconciliation: GET /v1/budget after the burst ==
client allowed_sum (5840) + spent_before (0) = 5840
server company_spent_today after burst = 5840
OK: total allowed ($5840) <= company_daily_ceiling ($6000)
```

Every one of the 10 blocked requests cited `"rule": "Company daily ceiling reached"`, with the
exact running total in `why`, e.g. `"$5,840 + $210 > $6,000"`. The client-side allowed sum
($5,840) matched the server's own `company_spent_today` exactly, and the total stayed at or
under the $6,000 ceiling.

A separate, earlier run against a different fresh workspace on the same day produced:

| Run | Requests | Allowed | Allowed sum | Blocked | Ceiling |
|-----|----------|---------|-------------|---------|---------|
| A (reset, then burst again) | 40 | 27 | $5,720 (+$180 earlier spend = $5,900 total) | 13 | $6,000 |
| B (same workspace, day reset) | 40 | 32 | $6,000 | 8 | $6,000 |
| C (this script, fresh workspace) | 40 | 30 | $5,840 | 10 | $6,000 |

In all three runs, every blocked request cited the shared ceiling specifically, and the server's
own ledger matched the client-observed total exactly - no run went over $6,000.

## How to read the result

- `allowed_sum` (plus whatever was already spent that day) should never exceed
  `company_daily_ceiling`.
- Every blocked request's `rule` should say `"Company daily ceiling reached"`, not a per-agent
  rule - that is how you know the ceiling, not something else, is what stopped it.
- The script asserts both of these itself and will raise an `AssertionError` if either one is
  violated.

## Limits

- Sandbox only: fake money, test credentials, production is not available.
- One test environment, one template (`coffee`), 40 requests, 3 agents. This is not a
  large-scale concurrency stress test (hundreds of parallel agents) and it only ran against one
  sandbox instance, so it cannot distinguish "the ceiling check is inherently atomic" from "this
  instance's concurrency was low enough that a non-atomic check rarely races."
- This script makes no claims about how the ceiling is implemented internally - it only reports
  what the API returned.

## Docs

- Developer docs: https://pinkwallet.com/agentic/developers/?utm_source=github&utm_medium=example&utm_campaign=shared-ceiling-test
- Sandbox: https://agentic-sandbox.pinkwallet.com
- Root of this repo: [`../README.md`](../README.md)

Maintained by the PinkWallet team.
