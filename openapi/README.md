# OpenAPI spec — Pink Agentic AI Payments sandbox

[`openapi.yaml`](openapi.yaml) is an OpenAPI 3.1 description of the sandbox's REST API
(`https://agentic-sandbox.pinkwallet.com/v1/*`). The same functionality is also available
as an MCP server — see the main [README](../README.md) and
[`llms-install.md`](../llms-install.md) for that.

**Sandbox only: test credentials, no real money moves, production is not available.**

It covers every agent-facing REST operation (`/v1/me`, `/v1/budget`, `/v1/payees`,
`/v1/vaults`, `/v1/rules`, `/v1/payments/check`, `/v1/payments`, `/v1/payments/{id}`,
`/v1/payments/{id}/receipt`) and the no-auth `POST /v1/sandbox/workspaces` signup call, plus
the admin routes under `/v1/admin/*`. Every example in the spec is a real (secret-redacted)
response captured against the live sandbox — see
`/Users/qishi/pinkwallet-growth/data/deliverables/dev-surface/openapi/REPORT.md` in the
pinkwallet-growth workspace for the full contract-test log, or re-run the two calls below
yourself.

- Lint: `npx -y @redocly/cli lint openapi.yaml` — 0 errors, 1 informational warning
  (the no-auth signup endpoint has no documented 4xx because malformed JSON bodies return
  `500`, verified live; see the comment above that operation in the spec).
- Live contract test: every documented operation was called against the live sandbox and
  its real response body validated against this spec's JSON Schema (23/23 passed). `PUT
  /v1/admin/rules` and `POST /v1/admin/reset` are documented from source + the founder's own
  `test/smoke.mjs` rather than independently re-run here, to stay within a 2-workspace budget.

## Import into Postman

Postman → **Import** → **Link** (or drag the file) → paste the path/URL to `openapi.yaml`
(e.g. the raw GitHub URL below). Postman creates a collection with one request per operation
and a `bearerToken` variable you can set to an agent or admin key from
`POST /v1/sandbox/workspaces`.

Raw file for import tools that take a URL:
`https://raw.githubusercontent.com/Pink-Agentic-Payments/sandbox-examples/main/openapi/openapi.yaml`

## Import as a ChatGPT custom GPT Action

1. In the GPT editor, **Configure → Create new action**.
2. **Import from URL** → paste the raw URL above (or paste the YAML directly).
3. Authentication → **API Key** → **Bearer**, and paste an agent key you got from
   `POST /v1/sandbox/workspaces` (no auth needed for that one call — curl it first, or use
   `01-curl/quickstart.sh` in the parent directory).
4. The action will expose `createSandboxWorkspace`, `getBudget`, `checkPayment`,
   `requestPayment`, etc. as callable tools. Note ChatGPT Actions require one auth scheme per
   action — if you want both agent-key and admin-key operations, split into two actions (or
   two GPTs), since this spec mixes `agentKey` and `adminKey` bearer schemes per-operation.

## Any other OpenAPI-aware client

Point it at the raw URL above, or the local file. Everything under `/v1/*` needs
`Authorization: Bearer <key>` except `POST /v1/sandbox/workspaces`, which is open — that's how
you get a key in the first place.
