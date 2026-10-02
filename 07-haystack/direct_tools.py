"""Pink Agentic AI Payments — direct MCP tool calls, no LLM (sandbox only, no money moves)

Loads the Pink tools through the official `mcp-haystack` integration
(MCPToolset over Streamable HTTP) and calls `pink.request_payment` directly,
so anyone can verify the MCP server and the policy engine work without
needing a model API key. Runs the same 3 scenarios as agent.py: one small
payment (allowed), one bigger one (pending_human), one to a blocked payee
category (blocked).

Usage: PINK_AGENT_KEY=pk_sandbox_agent_... python3 direct_tools.py
"""
import json
import os

from haystack_integrations.tools.mcp import MCPToolset, StreamableHttpServerInfo

MCP_URL = "https://agentic-sandbox.pinkwallet.com/mcp"


def main() -> None:
    agent_key = os.environ.get("PINK_AGENT_KEY")
    if not agent_key:
        raise SystemExit(
            "Set PINK_AGENT_KEY to a pk_sandbox_agent_... key (see ../01-curl/quickstart.sh)."
        )

    server_info = StreamableHttpServerInfo(url=MCP_URL, token=agent_key)
    # eager_connect=True so the toolset connects and lists tools right away,
    # instead of deferring to a Pipeline's warm_up() step.
    toolset = MCPToolset(server_info=server_info, eager_connect=True)

    tools_by_name = {t.name: t for t in toolset}
    print("== Tools available ==")
    print(", ".join(sorted(tools_by_name)))

    request_payment = tools_by_name["pink.request_payment"]

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
        result = request_payment.invoke(**args)
        # MCPTool.invoke() returns the raw MCP CallToolResult as a JSON string;
        # the tool's actual JSON reply is nested in content[0]["text"].
        envelope = json.loads(result)
        data = json.loads(envelope["content"][0]["text"])
        print(f"decision={data['decision']}  rule={data.get('rule') or data.get('why')}")
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
