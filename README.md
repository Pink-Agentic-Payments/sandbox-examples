# Pink Agentic AI Payments — sandbox examples

**Pink Agentic AI Payments** (by PinkWallet, early access) is the approval layer between AI agents and company money: plain-language rules, per-agent budgets and human approvals decide each payment before a one-time card or bank transfer is issued.

**Sandbox only: test credentials, no money moves, production not available.**

This repo has four tiny, runnable clients against the live public sandbox at **https://agentic-sandbox.pinkwallet.com** — curl, the official MCP SDK (Node), plain REST (Python stdlib), and a small agent loop that shows all three outcomes an agent can get: `allowed`, `pending_human`, `blocked`.

> The sandbox's "coffee shop" template includes a night-time rule (23:00–06:00 local → ask the owner). That means the decision for the exact same payment can change depending on when you run it. Every example below passes `local_hour` explicitly so the outputs are reproducible — but they still **print** the decision instead of assuming it, which is the point: policy is evaluated per request, not hardcoded.

## Quickstart (2 minutes)

```bash
# 1. Create a free sandbox workspace and get an agent key
curl -s -X POST https://agentic-sandbox.pinkwallet.com/v1/sandbox/workspaces \
  -H "Content-Type: application/json" \
  -d '{"company":"My Test Co","email":"","template":"coffee"}'

# 2. Export the agent key it returns (agents[].key, looks like pk_sandbox_agent_...)
export PINK_AGENT_KEY=pk_sandbox_agent_...

# 3. Run any example below
./01-curl/quickstart.sh
```

## Use with Cline

This server works as a remote MCP server (Streamable HTTP). See [`llms-install.md`](llms-install.md) for the full autonomous setup (create a sandbox workspace, get a key, verify the connection). The Cline config ([remote MCP server format](https://docs.cline.bot/mcp/configuring-mcp-servers)) is:

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

## Examples

| Example | What it does | Command |
|---|---|---|
| [`01-curl/`](01-curl) | Creates a workspace, reads the budget, dry-runs and makes a payment with plain curl + jq | `./01-curl/quickstart.sh` |
| [`02-node-mcp/`](02-node-mcp) | Connects over MCP (Streamable HTTP) with the official `@modelcontextprotocol/sdk`, lists tools, calls `pink.check_policy` + `pink.request_payment` | `PINK_AGENT_KEY=... node index.mjs` |
| [`03-python-rest/`](03-python-rest) | Same flow over plain REST using only Python's standard library (`urllib`); checks, pays, and polls a pending payment | `PINK_AGENT_KEY=... python3 pay.py` |
| [`04-agent-loop/`](04-agent-loop) | ~60-line loop that buys 3 things: one small order (allowed), one bigger order (pending human approval), one to a blocked category (blocked) | `PINK_AGENT_KEY=... node agent-loop.mjs` |
| [`05-langgraph/`](05-langgraph) | A [LangGraph](https://github.com/langchain-ai/langgraph) ReAct agent + `langchain-mcp-adapters`, 3 scenarios (allowed / pending_human / blocked) incl. a prompt-injection probe that gets blocked server-side | `PINK_AGENT_KEY=... GEMINI_API_KEY=... python3 05-langgraph/react_agent.py` |
| [`06-openai-agents-sdk/`](06-openai-agents-sdk) | An [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) agent + `MCPServerStreamableHttp`, same 3 scenarios, OpenAI-first with a Gemini/LiteLLM fallback | `PINK_AGENT_KEY=... OPENAI_API_KEY=... python3 06-openai-agents-sdk/agent.py` |
| [`07-haystack/`](07-haystack) | A [Haystack](https://github.com/deepset-ai/haystack) `Agent` + the official `mcp-haystack` `MCPToolset`, same 3 scenarios, Gemini chat generator | `PINK_AGENT_KEY=... GEMINI_API_KEY=... python3 07-haystack/agent.py` |
| [`openapi/`](openapi) | OpenAPI 3.1 spec for the REST API, live-validated against the sandbox; import into Postman or a ChatGPT custom GPT Action | `npx -y @redocly/cli lint openapi/openapi.yaml` |

Each example needs an agent key for the **coffee** template (`a_purch`, `a_inv`, `a_mkt`, or `a_pay` — see `01-curl/quickstart.sh` to create a workspace and get one).

### 1. curl — real run, 2026-10-01

```
$ ./quickstart.sh
== 3. Dry-run a payment (nothing is spent) ==
{
  "decision": "would_allow",
  "reason": "Small supply orders go through",
  ...
}

== 4. Make the real payment (sandbox credential, no money moves) ==
{
  "payment_id": "pay_6c2248fe8a03",
  "decision": "allowed",
  "agent": "Purchasing AI",
  "payee": "Sysco",
  "amount": 150,
  "currency": "USD",
  "rule": "Small supply orders go through",
  "credential": {
    "type": "virtual_card",
    "sandbox": true,
    "max_amount": 150,
    "single_use": true,
    "card": { "pan": "4111 1111 3954 9741", "exp": "12/27", "cvv": "467", "name": "PINK SANDBOX" }
  }
}
```

### 2. Node MCP SDK — real run, 2026-10-01

```
$ PINK_AGENT_KEY=pk_sandbox_agent_hoa8… node index.mjs
== Tools available ==
pink.get_budget, pink.list_payees, pink.list_rules, pink.check_policy, pink.request_payment, pink.get_credential, pink.report_receipt

== pink.request_payment ==
{
  "payment_id": "pay_eb1692583f46",
  "decision": "allowed",
  "agent": "Inventory AI",
  "payee": "Sysco",
  "amount": 150,
  "rule": "Small supply orders go through",
  "credential": { "type": "virtual_card", "sandbox": true, "max_amount": 150, "single_use": true, "card": { "pan": "4111 1111 8247 6657", "exp": "12/27", "cvv": "732", "name": "PINK SANDBOX" } }
}
```

### 3. Python REST (stdlib only) — real run, 2026-10-01

```
$ PINK_AGENT_KEY=pk_sandbox_agent_hoa8… python3 pay.py
== Make the payment ==
202 {
  "payment_id": "pay_e6d89cee7384",
  "decision": "pending_human",
  "agent": "Payroll & Bills AI",
  "payee": "Uline",
  "amount": 2200,
  "rule": "Anything over $2,000: ask the owner",
  "hold_id": "pay_e6d89cee7384",
  "approvers_needed": 1,
  "who": "Maya Chen (Owner)",
  "poll": "pink.get_credential(hold_id) · or GET /v1/payments/{id}"
}

== Polling pending payment pay_e6d89cee7384 ==
attempt 1: 200 pending_human
attempt 2: 200 pending_human
attempt 3: 200 pending_human
```
(It stays `pending_human` until a person approves it in the console — that's the point of the approval layer.)

### 4. Agent loop — real run, 2026-10-01

```
$ PINK_AGENT_KEY=pk_sandbox_agent_hoa8… node agent-loop.mjs
[allowed] p_sysco $80 — Small supply orders go through
[pending_human] p_uline $900 — Bigger supply orders: store manager checks
[blocked] Quick Gift Cards LLC $50 — Never: gift cards, cash-like, crypto
```

## Docs & registry

- Developer docs: https://pinkwallet.com/agentic/developers/
- MCP Registry: `com.pinkwallet/agentic-payments-sandbox`
- Public sandbox: https://agentic-sandbox.pinkwallet.com

Maintained by the PinkWallet team.
