#!/usr/bin/env python3
"""
shared_ceiling_test.py

Checks whether the Pink Agentic AI Payments sandbox enforces a *shared*
company daily ceiling correctly when several different agents fire payment
requests at the same time, not just one agent at a time.

It creates a disposable sandbox workspace (template "coffee", which seeds
3 usable agents: a_purch, a_inv, a_pay, all drawing against one company
daily ceiling), reads each agent's own budget, plans payment amounts so
that only the shared ceiling (not any agent's own monthly budget or
per-payment cap) can block a request, then fires at least 40 of those
requests concurrently from all 3 agents at once.

Usage:
    python3 shared_ceiling_test.py

Requires: requests (pip install requests). No API key to set up: the
script creates its own sandbox workspace each run and never prints a raw
agent key (only a masked pk_sandb...XXXX excerpt).
"""
import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE = "https://agentic-sandbox.pinkwallet.com"
LOCAL_HOUR = 14  # avoid the coffee template's 11pm-6am "ask owner" rule
AGENT_IDS = ["a_purch", "a_inv", "a_pay"]  # a_mkt deliberately excluded: see README


def mask(key):
    return f"{key[:12]}...{key[-4:]}"


def create_workspace():
    r = requests.post(
        f"{BASE}/v1/sandbox/workspaces",
        json={"template": "coffee", "company": "GitHub Example - Shared Ceiling Test"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def get_budget(agent_key):
    r = requests.get(f"{BASE}/v1/budget", headers={"Authorization": f"Bearer {agent_key}"}, timeout=20)
    r.raise_for_status()
    return r.json()


def plan_requests(budgets):
    """Pick per-agent amount/count so the shared ceiling is the only thing
    that can block a request. Each agent's own share is kept well inside
    its single_payment_cap and left_this_month."""
    ceiling = budgets["a_purch"]["company_daily_ceiling"]
    company_spent_today = budgets["a_purch"]["company_spent_today"]
    room = ceiling - company_spent_today

    # a_purch: 4 requests, small fraction of its own per-payment cap
    amt_purch = min(100, budgets["a_purch"]["single_payment_cap"] // 2)
    n_purch = 4

    # a_inv: 2 requests, same idea
    amt_inv = min(200, budgets["a_inv"]["single_payment_cap"] // 1 - 100)
    n_inv = 2

    # a_pay: the remaining 34 requests, sized so requested_sum lands ~25-30%
    # over the ceiling, while staying far under a_pay's own monthly budget
    # and per-payment cap (both are large on this template).
    n_pay = 34
    target_total = round(room * 1.3) if room > 0 else round(ceiling * 1.3)
    remaining = max(target_total - (amt_purch * n_purch + amt_inv * n_inv), n_pay * 10)
    amt_pay = max(10, round((remaining / n_pay) / 10) * 10)
    amt_pay = min(amt_pay, budgets["a_pay"]["single_payment_cap"])

    plan = [
        {"agent_id": "a_purch", "payee": "p_cc", "amount": amt_purch, "n": n_purch},
        {"agent_id": "a_inv", "payee": "p_cc", "amount": amt_inv, "n": n_inv},
        {"agent_id": "a_pay", "payee": "p_gusto", "amount": amt_pay, "n": n_pay},
    ]

    # Sanity check: no agent's own share should come close to its own limits.
    for p in plan:
        b = budgets[p["agent_id"]]
        own_sum = p["amount"] * p["n"]
        assert p["amount"] <= b["single_payment_cap"], f"{p['agent_id']}: amount exceeds its own per-payment cap"
        assert own_sum <= b["left_this_month"] * 0.5, f"{p['agent_id']}: own share too close to its own monthly budget"

    return plan, ceiling, company_spent_today


def fire(workspace_id, run_tag, agent_key, agent_id, payee, amount, i):
    idem = f"sharedceil-{workspace_id}-{run_tag}-{agent_id}-{i}-{uuid.uuid4().hex[:8]}"
    r = requests.post(
        f"{BASE}/v1/payments",
        headers={"Authorization": f"Bearer {agent_key}", "Content-Type": "application/json"},
        json={
            "payee_id": payee,
            "amount": amount,
            "purpose": f"shared-ceiling-test-{agent_id}-{i}",
            "idempotency_key": idem,
            "local_hour": LOCAL_HOUR,
        },
        timeout=20,
    )
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text}
    return {
        "agent_id": agent_id,
        "requested_amount": amount,
        "status": r.status_code,
        "decision": body.get("decision"),
        "amount": body.get("amount"),
        "rule": body.get("rule"),
        "why": body.get("why"),
    }


def main():
    print("== Creating sandbox workspace (template=coffee) ==")
    ws = create_workspace()
    workspace_id = ws["workspace_id"]
    agents = {a["id"]: a for a in ws["agents"] if a["id"] in AGENT_IDS}
    print(f"Workspace: {workspace_id}")
    for aid, a in agents.items():
        print(f"  {aid}: {mask(a['key'])}")

    print("\n== Reading each agent's budget (GET /v1/budget) ==")
    budgets = {aid: get_budget(a["key"]) for aid, a in agents.items()}
    for aid, b in budgets.items():
        print(f"  {aid}: left_this_month={b['left_this_month']} single_payment_cap={b['single_payment_cap']}")
    ceiling = budgets["a_purch"]["company_daily_ceiling"]
    print(f"  company_daily_ceiling={ceiling} company_spent_today={budgets['a_purch']['company_spent_today']}")

    plan, ceiling, spent_before = plan_requests(budgets)
    jobs = []
    for p in plan:
        for i in range(p["n"]):
            jobs.append({**p, "i": i})
    requested_sum = sum(j["amount"] for j in jobs)
    print(f"\n== Plan: {len(jobs)} requests across {len(plan)} agents, requested_sum=${requested_sum} vs ceiling=${ceiling} ==")
    for p in plan:
        print(f"  {p['agent_id']}: {p['n']} x ${p['amount']} = ${p['n'] * p['amount']}")

    print(f"\n== Firing {len(jobs)} requests concurrently ==")
    results = []
    with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
        futs = [
            ex.submit(fire, workspace_id, "run1", agents[j["agent_id"]]["key"], j["agent_id"], j["payee"], j["amount"], j["i"])
            for j in jobs
        ]
        for f in as_completed(futs):
            results.append(f.result())

    allowed = [r for r in results if r["status"] == 201]
    blocked = [r for r in results if r["status"] == 403]
    other = [r for r in results if r["status"] not in (201, 403)]
    allowed_sum = sum(r["amount"] for r in allowed if r["amount"] is not None)

    blocked_by_rule = {}
    for r in blocked:
        rule = r.get("rule") or "unknown"
        blocked_by_rule[rule] = blocked_by_rule.get(rule, 0) + 1

    summary = {
        "workspace_id": workspace_id,
        "n_requests": len(jobs),
        "requested_sum": requested_sum,
        "allowed_count": len(allowed),
        "allowed_sum": allowed_sum,
        "blocked_count": len(blocked),
        "blocked_by_rule": blocked_by_rule,
        "other_count": len(other),
        "company_daily_ceiling": ceiling,
        "company_spent_today_before": spent_before,
    }
    print("\n== Summary ==")
    print(json.dumps(summary, indent=2))

    print("\n== Sample blocked responses ==")
    for r in blocked[:3]:
        print(json.dumps(r, indent=2))

    print("\n== Reconciliation: GET /v1/budget after the burst ==")
    after = get_budget(agents["a_purch"]["key"])
    company_spent_today_after = after["company_spent_today"]
    print(f"client allowed_sum ({allowed_sum}) + spent_before ({spent_before}) = {allowed_sum + spent_before}")
    print(f"server company_spent_today after burst = {company_spent_today_after}")
    assert allowed_sum + spent_before == company_spent_today_after, "client/server totals disagree"
    assert company_spent_today_after <= ceiling, "ceiling was exceeded"
    print(f"OK: total allowed (${company_spent_today_after}) <= company_daily_ceiling (${ceiling})")


if __name__ == "__main__":
    main()
