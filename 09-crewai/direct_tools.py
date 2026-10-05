"""Pink Agentic AI Payments — direct MCP tool calls, no LLM (sandbox only, no money moves)

Loads the Pink tools through crewai-tools' MCPServerAdapter and calls
pink.request_payment directly, so anyone can verify the MCP server and the
policy engine work without needing a model API key. Runs the same 3
scenarios as crewai_agent.py: one small payment (allowed), one bigger one
(pending_human), one to a blocked payee category (blocked).

Usage: PINK_AGENT_KEY=pk_sandbox_agent_... python3 direct_tools.py
"""
import json
import os

from crewai_tools import MCPServerAdapter

MCP_URL = "https://agentic-sandbox.pinkwallet.com/mcp"


def _strip_nulls(tool) -> None:
    """Work around a CrewAI MCP adapter quirk (crewai-tools 1.15.23).

    CrewAI's BaseTool.run() validates kwargs against the tool's generated
    pydantic schema and always model_dump()s every field, including unset
    optional ones, which come out as `None`. Those get sent to the MCP
    server as JSON `null`. The Pink MCP server's schema defines those
    fields as optional-but-absent (e.g. `payee_name` only required if
    `payee_id` is omitted) and rejects an explicit `null`. This patches
    the tool's class-level `_run` to drop `None` values before the call.
    """
    original_run = type(tool)._run

    def patched_run(self, **kwargs):
        clean = {k: v for k, v in kwargs.items() if v is not None}
        return original_run(self, **clean)

    type(tool)._run = patched_run


def main() -> None:
    agent_key = os.environ.get("PINK_AGENT_KEY")
    if not agent_key:
        raise SystemExit(
            "Set PINK_AGENT_KEY to a pk_sandbox_agent_... key (see ../01-curl/quickstart.sh)."
        )

    server_params = {
        "url": MCP_URL,
        "transport": "streamable-http",
        "headers": {"Authorization": f"Bearer {agent_key}"},
    }

    # The coffee template has a night-time rule (23:00-06:00 local -> ask the
    # owner). We pass local_hour=14 on every call so these three outcomes are
    # deterministic no matter when you run this.
    scenarios = [
        ("allowed", {"payee_id": "p_sysco", "amount": 80, "purpose": "Weekly syrup top-up", "local_hour": 14}),
        ("pending_human", {"payee_id": "p_uline", "amount": 900, "purpose": "Bulk cup and lid order", "local_hour": 14}),
        ("blocked", {"payee_name": "Quick Gift Cards LLC", "amount": 50, "purpose": "Buy gift cards", "local_hour": 14}),
    ]

    with MCPServerAdapter(server_params) as tools:
        by_name = {t.name: t for t in tools}
        print("== Tools available ==")
        print(", ".join(sorted(by_name)))

        request_payment = by_name["pink_request_payment"]
        _strip_nulls(request_payment)

        for label, args in scenarios:
            print(f"\n== expecting {label}: pink.request_payment({args}) ==")
            text = request_payment.run(**args)
            data = json.loads(text)
            print(f"decision={data['decision']}  rule={data.get('rule') or data.get('why')}")
            print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
