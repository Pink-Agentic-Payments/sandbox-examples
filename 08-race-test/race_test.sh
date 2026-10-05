#!/usr/bin/env bash
# race_test.sh
# Fires N parallel payments at the Pink Agentic AI Payments sandbox against
# a single agent's daily spending rule, then reports how many were allowed
# vs blocked and what the server recorded as spent_today.
#
# Usage: ./race_test.sh [N] [AMOUNT]
#   N      number of parallel payment requests to fire (default 40)
#   AMOUNT dollar amount per payment (default 7)
#
# Requires: curl, python3. No secrets are stored; this script creates its
# own disposable sandbox workspace each run and prints no raw agent key.

set -euo pipefail

BASE="https://agentic-sandbox.pinkwallet.com"
UA="curl/8.4.0"
N="${1:-40}"
AMOUNT="${2:-7}"

echo "== Creating sandbox workspace (template=startup) =="
WORKSPACE_JSON=$(curl -s -A "$UA" -X POST "$BASE/v1/sandbox/workspaces" \
  -H 'content-type: application/json' \
  -d '{"template":"startup","company":"race-test"}')

AGENT_KEY=$(python3 -c '
import json, sys
data = json.loads(sys.stdin.read())
agents = data.get("agents", data.get("workspace", {}).get("agents", []))
for a in agents:
    if a.get("id") == "a_eng" or "eng" in str(a.get("id", "")).lower():
        print(a.get("key") or a.get("agent_key") or a.get("api_key"))
        sys.exit(0)
# fallback: first agent with a key
for a in agents:
    k = a.get("key") or a.get("agent_key") or a.get("api_key")
    if k:
        print(k)
        sys.exit(0)
sys.exit(1)
' <<< "$WORKSPACE_JSON")

if [ -z "$AGENT_KEY" ]; then
  echo "Could not extract agent key. Raw response:"
  echo "$WORKSPACE_JSON"
  exit 1
fi

MASKED_KEY="${AGENT_KEY:0:8}...${AGENT_KEY: -4}"
echo "Workspace created. Using agent key: $MASKED_KEY"
echo "Payee: p_anth, amount: \$$AMOUNT, requests: $N (fired in parallel)"
echo ""

RESULTS_DIR=$(mktemp -d)
trap 'rm -rf "$RESULTS_DIR"' EXIT

echo "== Firing $N parallel payment requests =="
for i in $(seq 1 "$N"); do
  curl -s -A "$UA" -X POST "$BASE/v1/payments" \
    -H "Authorization: Bearer $AGENT_KEY" \
    -H 'content-type: application/json' \
    -d "{\"payee_id\":\"p_anth\",\"amount\":$AMOUNT,\"purpose\":\"race test $i\",\"local_hour\":12}" \
    > "$RESULTS_DIR/resp_$i.json" &
done
wait

ALLOWED=0
BLOCKED=0
OTHER=0
for f in "$RESULTS_DIR"/resp_*.json; do
  STATUS=$(python3 -c '
import json, sys
try:
    d = json.loads(open(sys.argv[1]).read())
    print(d.get("decision") or d.get("status") or "unknown")
except Exception:
    print("parse_error")
' "$f")
  case "$STATUS" in
    allow|allowed) ALLOWED=$((ALLOWED+1)) ;;
    block|blocked) BLOCKED=$((BLOCKED+1)) ;;
    *) OTHER=$((OTHER+1)) ;;
  esac
done

echo ""
echo "== Results =="
echo "Allowed: $ALLOWED"
echo "Blocked: $BLOCKED"
echo "Other/unparsed: $OTHER"
echo "Expected total spend if all allowed: \$$((N * AMOUNT))"
echo "Allowed spend: \$$((ALLOWED * AMOUNT))"

echo ""
echo "== Fetching /v1/budget =="
BUDGET_JSON=$(curl -s -A "$UA" "$BASE/v1/budget" -H "Authorization: Bearer $AGENT_KEY")
echo "$BUDGET_JSON"

echo ""
echo "== Done =="
