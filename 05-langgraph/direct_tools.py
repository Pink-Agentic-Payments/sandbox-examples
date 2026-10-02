"""Pink Agentic AI Payments — direct MCP tool calls, no LLM (sandbox only, no money moves)

Loads the Pink tools through langchain-mcp-adapters and calls them directly,
so anyone can verify the MCP server and the policy engine work without
needing a model API key. Runs the same 3 scenarios as react_agent.py:
one small payment (allowed), one bigger one (pending_human), one to a
blocked payee category (blocked).

Usage: PINK_AGENT_KEY=pk_sandbox_agent_... python3 direct_tools.py
"""
import asyncio
import json
import os

from langchain_mcp_adapters.client import MultiServerMCPClient

MCP_URL = "https://agentic-sandbox.pinkwallet.com/mcp"


async def main() -> None:
    agent_key = os.environ.get("PINK_AGENT_KEY")
    if not agent_key:
        raise SystemExit(
            "Set PINK_AGENT_KEY to a pk_sandbox_agent_... key (see ../01-curl/quickstart.sh)."
        )

    client = MultiServerMCPClient(
        {
            "pink": {
                "url": MCP_URL,
                "transport": "streamable_http",
                "headers": {"Authorization": f"Bearer {agent_key}"},
            }
        }
    )
    tools = {t.name: t for t in await client.get_tools()}
    print("== Tools available ==")
    print(", ".join(sorted(tools)))

    request_payment = tools["pink.request_payment"]

    # The coffee template has a night-time rule (23:00-06:00 local -> ask the
    # owner). We pass local_hour=14 on every call so these three outcomes are
    # deterministic no matter when you run this.
    scenarios = [
        ("allowed", {"payee_id": "p_sysco", "amount": 80, "purpose": "Weekly syrup top-up", "local_hour": 14}),
        ("pending_human", {"payee_id": "p_uline", "amount": 900, "purpose": "Bulk cup and lid order", "local_hour": 14}),
        ("blocked", {"payee_name": "Quick Gift Cards LLC", "amount": 50, "purpose": "Buy gift cards", "local_hour": 14}),
    ]

    for label, args in scenarios:
        print(f"\n== expecting {label}: pink.request_payment({args}) ==")
        result = await request_payment.ainvoke(args)
        text = result[0]["text"] if isinstance(result, list) else result
        data = json.loads(text)
        print(f"decision={data['decision']}  rule={data.get('rule') or data.get('why')}")
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
