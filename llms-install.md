# Installing Pink Agentic AI Payments (sandbox) for Cline

This file is written for an AI agent (e.g. Cline) to follow autonomously. No human input is required beyond running the commands below.

> **Sandbox only.** This connects to a public test sandbox. Credentials returned here are test values (`pk_sandbox_agent_...`); no real money moves. This is an early-access PinkWallet product and production is not available yet.

## 1. Create a free sandbox workspace and get an agent key

Run:

```bash
curl -s -X POST https://agentic-sandbox.pinkwallet.com/v1/sandbox/workspaces \
  -H "Content-Type: application/json" \
  -d '{"company":"My Test Co","email":"","template":"coffee"}'
```

The response is JSON with an `agents` array. Each entry has a `key` field that looks like `pk_sandbox_agent_...` — read any one of them (e.g. `agents[0].key`, the "Purchasing AI" agent). This key is the bearer token for the MCP server.

## 2. Add the server to Cline's MCP settings

Add this block to `cline_mcp_settings.json` (Cline's remote MCP config format, Streamable HTTP — see [Cline docs: Configuring MCP Servers](https://docs.cline.bot/mcp/configuring-mcp-servers) for the field reference):

```json
{
  "mcpServers": {
    "pink-agentic-payments-sandbox": {
      "type": "streamableHttp",
      "url": "https://agentic-sandbox.pinkwallet.com/mcp",
      "headers": {
        "Authorization": "Bearer pk_sandbox_agent_REPLACE_ME"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Replace `pk_sandbox_agent_REPLACE_ME` with the key you read in step 1. Without a valid key the server returns `401`.

## 3. Verify the connection

List the server's tools (`tools/list`) and confirm these names are present: `pink.get_budget`, `pink.list_payees`, `pink.list_rules`, `pink.check_policy`, `pink.request_payment`, `pink.get_credential`, `pink.report_receipt`.

Then call the budget tool to confirm the connection works end-to-end:

```
pink.get_budget
```

with no arguments. A working connection returns JSON like:

```json
{
  "agent": "Purchasing AI",
  "status": "active",
  "monthly_budget": 4000,
  "spent_this_month": 2260,
  "left_this_month": 1740,
  "vault": { "id": "v_ops", "name": "Operating", "balances": { "USD": 18420.55 } }
}
```

## Sandbox-only note

- Test credentials only. No real money moves. Values (balances, cards) are illustrative sandbox data, regenerated per workspace.
- The `coffee` template includes a night-time rule: between 23:00–06:00 local time, payments require "ask the owner" (`pending_human`) instead of auto-approving. Because this depends on wall-clock time, pass `local_hour` explicitly to `pink.check_policy` / `pink.request_payment` when you want reproducible results (see `01-curl/quickstart.sh` and `04-agent-loop/agent-loop.mjs` in this repo for examples) — otherwise the decision can differ depending on when you run it.
- This product is early access. The public sandbox is for development and demos only; there is no production environment yet.
