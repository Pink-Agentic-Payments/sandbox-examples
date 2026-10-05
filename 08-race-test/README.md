# Race test: 40 parallel payments against one daily rule (sandbox only, no money moves)

`race_test.sh` checks whether the **Pink Agentic AI Payments** sandbox enforces a per-agent daily
spending rule correctly when many payment requests land at the same time, not just one at a time.
It creates a disposable sandbox workspace, then fires 40 `$7` payment requests at the sandbox
**in parallel** (all 40 `curl` calls backgrounded and launched together) from a single agent whose
rule caps it at **$200/day**, and counts how many the server allowed vs. blocked.

If the rule were only checked after the fact, or checked with a race condition in the server's
accounting, you'd expect to see more than `$200` worth of payments allowed. What we actually
observed: the server allowed exactly as many payments as fit under the cap and blocked the rest,
every time.

**Sandbox only: test credentials, no money moves, production not available.**

## What it does

1. `POST /v1/sandbox/workspaces` creates a fresh `startup`-template sandbox workspace with test
   money and an agent, `a_eng` ("Eng Infra AI"), whose rule is **"API credits: $200 a day per
   agent, then stop."**
2. The script fires 40 `POST /v1/payments` requests in parallel, each for `$7` to payee `p_anth`
   (so if every request were allowed, that would be `$280`, well over the `$200` daily cap).
3. It counts how many came back `allowed` vs. `blocked`, and prints the totals plus the expected
   spend if the cap hadn't held.
4. It fetches `GET /v1/budget` afterward and prints the server's own `spent_today`, so you can
   check it against the allowed count yourself.

## How to run

```bash
./race_test.sh [N] [AMOUNT]
# N      number of parallel payment requests to fire (default 40)
# AMOUNT dollar amount per payment (default 7)

./race_test.sh        # default: 40 requests x $7
./race_test.sh 40 7   # explicit, same as above
```

Requires `curl` and `python3`. No API key to set up: the script creates its own sandbox workspace
each run and never prints a raw agent key (only a masked `pk_sandb...XXXX` excerpt).

## Real results (see `TEST-LOG.md` for full transcripts)

Three independent runs of `./race_test.sh 40 7`, each against a fresh sandbox workspace:

| Run | Requests | Allowed | Blocked | spent_today |
|-----|----------|---------|---------|--------------|
| 1   | 40 x $7  | 28      | 12      | $196         |
| 2   | 40 x $7  | 28      | 12      | $196         |
| 3 (publish verification) | 40 x $7 | 28 | 12 | $196 |

All three runs: **28 allowed ($196), 12 blocked**, and the server's own `/v1/budget` reports
`spent_today: 196`, matching the allowed count exactly. $196 is the largest multiple of $7 that
fits under the $200/day rule ($196 = 28 x $7; the 29th payment would put the agent at $203, over
the cap), so the sandbox's policy engine held the line under concurrent load rather than letting
the race condition overspend the daily rule.

## Docs

- Developer docs: https://pinkwallet.com/agentic/developers/?utm_source=github&utm_medium=example&utm_campaign=race-test
- Sandbox: https://agentic-sandbox.pinkwallet.com
- Root of this repo: [`../README.md`](../README.md)

Maintained by the PinkWallet team.
