#!/usr/bin/env bash
# Pink Agentic AI Payments — curl quickstart (sandbox only, no money moves)
#
# Creates a free sandbox workspace, reads the agent's budget, dry-runs a
# payment, then makes it for real and prints the decision.
#
# Requires: curl, jq
set -euo pipefail

BASE="https://agentic-sandbox.pinkwallet.com"

echo "== 1. Create a sandbox workspace (coffee template) =="
WORKSPACE_JSON=$(curl -s -X POST "$BASE/v1/sandbox/workspaces" \
  -H "Content-Type: application/json" \
  -d '{"company":"Quickstart Coffee Co","email":"","template":"coffee"}')

ADMIN_KEY=$(echo "$WORKSPACE_JSON" | jq -r '.admin_key')
AGENT_KEY=$(echo "$WORKSPACE_JSON" | jq -r '.agents[] | select(.id=="a_purch") | .key')
echo "Workspace: $(echo "$WORKSPACE_JSON" | jq -r '.workspace_id')"
echo "Agent key: ${AGENT_KEY:0:20}...(truncated)"
echo "Console:   $(echo "$WORKSPACE_JSON" | jq -r '.urls.console')"

echo
echo "== 2. Check the agent's budget =="
curl -s "$BASE/v1/budget" -H "Authorization: Bearer $AGENT_KEY" | jq .

echo
echo "== 3. Dry-run a payment (nothing is spent) =="
echo "Note: the coffee template has a night-time rule (23:00-06:00 local -> ask the owner)."
echo "We pass local_hour=14 to make this run deterministic regardless of when you run it."
curl -s -X POST "$BASE/v1/payments/check" \
  -H "Authorization: Bearer $AGENT_KEY" -H "Content-Type: application/json" \
  -d '{"payee_id":"p_sysco","amount":150,"purpose":"Milk and syrup restock","local_hour":14}' | jq .

echo
echo "== 4. Make the real payment (sandbox credential, no money moves) =="
curl -s -X POST "$BASE/v1/payments" \
  -H "Authorization: Bearer $AGENT_KEY" -H "Content-Type: application/json" \
  -H "Idempotency-Key: quickstart-$(date +%s)" \
  -d '{"payee_id":"p_sysco","amount":150,"purpose":"Milk and syrup restock","local_hour":14}' | jq .

echo
echo 'Done. Decision above: allowed (under the $500 small-order rule) -> a single-use virtual card was issued.'
