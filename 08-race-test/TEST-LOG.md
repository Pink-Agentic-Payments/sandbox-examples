# race_test.sh test log

Two independent runs of `race_test.sh 40 7` against the public sandbox
(`https://agentic-sandbox.pinkwallet.com`), each creating a fresh `startup`
template workspace and firing 40 simultaneous `$7` payments from agent
`a_eng` ("Eng Infra AI", rule: "API credits: $200 a day per agent, then
stop") to payee `p_anth`. Agent keys are masked below. This brings the
total sandbox workspaces created in this task to 3 (1 probe to check
response shapes + these 2 runs), within the 3-workspace limit.

## Run 1 (2026-10-05, ~05:05 UTC)

```
== Creating sandbox workspace (template=startup) ==
Workspace created. Using agent key: pk_sandb...24d3
Payee: p_anth, amount: $7, requests: 40 (fired in parallel)

== Firing 40 parallel payment requests ==

== Results ==
Allowed: 28
Blocked: 12
Other/unparsed: 0
Expected total spend if all allowed: $280
Allowed spend: $196

== Fetching /v1/budget ==
{
  "agent": "Eng Infra AI",
  "status": "active",
  "monthly_budget": 25000,
  "spent_this_month": 18036,
  "left_this_month": 6964,
  "spent_today": 196,
  "single_payment_cap": 1000,
  "vault": { "id": "v_cloud", "name": "Cloud & AI", "balances": { "USD": 58704 } },
  "company_daily_ceiling": 40000,
  "company_spent_today": 196,
  "policy_version": 1
}
```

## Run 2 (2026-10-05, ~05:06 UTC)

```
== Creating sandbox workspace (template=startup) ==
Workspace created. Using agent key: pk_sandb...10fc
Payee: p_anth, amount: $7, requests: 40 (fired in parallel)

== Firing 40 parallel payment requests ==

== Results ==
Allowed: 28
Blocked: 12
Other/unparsed: 0
Expected total spend if all allowed: $280
Allowed spend: $196

== Fetching /v1/budget ==
{
  "agent": "Eng Infra AI",
  "status": "active",
  "monthly_budget": 25000,
  "spent_this_month": 18036,
  "left_this_month": 6964,
  "spent_today": 196,
  "single_payment_cap": 1000,
  "vault": { "id": "v_cloud", "name": "Cloud & AI", "balances": { "USD": 58704 } },
  "company_daily_ceiling": 40000,
  "company_spent_today": 196,
  "policy_version": 1
}
```

## Summary

| Run | Requests | Allowed | Blocked | spent_today |
|-----|----------|---------|---------|--------------|
| 1   | 40 x $7  | 28      | 12      | $196         |
| 2   | 40 x $7  | 28      | 12      | $196         |
| 3 (publish verification) | 40 x $7 | 28 | 12 | $196 |

Both runs are identical to each other and match the prior PM-verified run
in `/Users/qishi/pinkwallet-growth/data/deliverables/dev-surface/concurrency-2026-10-04/EVIDENCE.md`
(line 4: "40 parallel POST /v1/payments, $7 to p_anth -> 28 allowed (sum
$196, rule r3), 12 blocked ... spent_today = 196").

## Run 3 - publish verification (2026-10-05, ~05:35 UTC)

Run by the distribution worker immediately before publishing this example to
`github.com/Pink-Agentic-Payments/sandbox-examples`, to confirm the script
still works unmodified against the live sandbox. Same command, same agent
(`a_eng`), a fresh workspace (4th sandbox workspace created across this
task's two work sessions).

```
== Creating sandbox workspace (template=startup) ==
Workspace created. Using agent key: pk_sandb...8802
Payee: p_anth, amount: $7, requests: 40 (fired in parallel)

== Firing 40 parallel payment requests ==

== Results ==
Allowed: 28
Blocked: 12
Other/unparsed: 0
Expected total spend if all allowed: $280
Allowed spend: $196

== Fetching /v1/budget ==
{
  "agent": "Eng Infra AI",
  "status": "active",
  "monthly_budget": 25000,
  "spent_this_month": 18036,
  "left_this_month": 6964,
  "spent_today": 196,
  "single_payment_cap": 1000,
  "vault": { "id": "v_cloud", "name": "Cloud & AI", "balances": { "USD": 58704 } },
  "company_daily_ceiling": 40000,
  "company_spent_today": 196,
  "policy_version": 1
}
```

Result: identical to Runs 1 and 2, 28 allowed / 12 blocked, $196 spent. Script
confirmed working as-is, no changes needed before publishing.

## Response shape notes (for script maintenance)

`POST /v1/sandbox/workspaces` returns `agents` as a top-level array, each
agent with `id`, `name`, `key`. `POST /v1/payments` returns a `decision`
field (`"allowed"` or `"blocked"`), not `status`. `GET /v1/budget` returns
`spent_today`, `spent_this_month`, `monthly_budget`, `single_payment_cap`.
Confirmed by direct probe requests before the two runs above.
