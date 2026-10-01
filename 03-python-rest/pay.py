#!/usr/bin/env python3
"""Pink Agentic AI Payments -- Python REST client example (sandbox only, no money moves).

Standard library only (urllib), Python 3.9+.

Usage:
    PINK_AGENT_KEY=pk_sandbox_agent_... python3 pay.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://agentic-sandbox.pinkwallet.com/v1"


def call(method, path, agent_key, body=None, extra_headers=None):
    headers = {
        "Authorization": f"Bearer {agent_key}",
        "Content-Type": "application/json",
        # Cloudflare blocks the default Python-urllib user agent.
        "User-Agent": "pink-agentic-payments-example/1.0",
    }
    headers.update(extra_headers or {})
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    agent_key = os.environ.get("PINK_AGENT_KEY")
    if not agent_key:
        print("Set PINK_AGENT_KEY to a pk_sandbox_agent_... key (see ../01-curl/quickstart.sh).")
        sys.exit(1)

    print("== Check a payment (dry run) ==")
    # The coffee template has a night-time rule (23:00-06:00 local -> ask the
    # owner). We pass local_hour explicitly so this example is deterministic.
    status, check = call(
        "POST", "/payments/check", agent_key,
        {"payee_id": "p_uline", "amount": 2200, "purpose": "Cup and lid restock", "local_hour": 14},
    )
    print(status, json.dumps(check, indent=2))

    print("\n== Make the payment ==")
    status, payment = call(
        "POST", "/payments", agent_key,
        {"payee_id": "p_uline", "amount": 2200, "purpose": "Cup and lid restock", "local_hour": 14},
        extra_headers={"Idempotency-Key": f"py-example-{int(time.time())}"},
    )
    print(status, json.dumps(payment, indent=2))

    if payment.get("decision") == "pending_human":
        payment_id = payment["payment_id"]
        print(f"\n== Polling pending payment {payment_id} ==")
        for attempt in range(3):
            time.sleep(2)
            status, polled = call("GET", f"/payments/{payment_id}", agent_key)
            print(f"attempt {attempt + 1}:", status, polled.get("decision"))
            if polled.get("decision") != "pending_human":
                print(json.dumps(polled, indent=2))
                break


if __name__ == "__main__":
    main()
