// Pink Agentic AI Payments — direct MCP tool calls, no LLM (sandbox only, no money moves)
//
// Connects to the sandbox MCP server with the Vercel AI SDK's MCP client
// (Streamable HTTP transport) and calls pink.request_payment directly, so
// anyone can verify the server and the policy engine work without needing
// a model API key. Runs the same 3 scenarios as ai-agent.mjs: one small
// payment (allowed), one bigger one (pending_human), one to a blocked
// payee category (blocked).
//
// Usage: PINK_AGENT_KEY=pk_sandbox_agent_... node direct-tools.mjs
import { createMCPClient } from '@ai-sdk/mcp';

const MCP_URL = 'https://agentic-sandbox.pinkwallet.com/mcp';
const agentKey = process.env.PINK_AGENT_KEY;
if (!agentKey) {
  console.error('Set PINK_AGENT_KEY to a pk_sandbox_agent_... key (see ../01-curl/quickstart.sh).');
  process.exit(1);
}

const client = await createMCPClient({
  transport: {
    type: 'http',
    url: MCP_URL,
    headers: { Authorization: `Bearer ${agentKey}` },
  },
});

const tools = await client.tools();
console.log('== Tools available ==');
console.log(Object.keys(tools).sort().join(', '));

const requestPayment = tools['pink.request_payment'];

// The coffee template has a night-time rule (23:00-06:00 local -> ask the
// owner). We pass local_hour=14 on every call so these three outcomes are
// deterministic no matter when you run this.
const scenarios = [
  ['allowed', { payee_id: 'p_sysco', amount: 80, purpose: 'Weekly syrup top-up', local_hour: 14 }],
  ['pending_human', { payee_id: 'p_uline', amount: 900, purpose: 'Bulk cup and lid order', local_hour: 14 }],
  ['blocked', { payee_name: 'Quick Gift Cards LLC', amount: 50, purpose: 'Buy gift cards', local_hour: 14 }],
];

for (const [label, args] of scenarios) {
  console.log(`\n== expecting ${label}: pink.request_payment(${JSON.stringify(args)}) ==`);
  const result = await requestPayment.execute(args, { toolCallId: label, messages: [] });
  const data = result.structuredContent ?? JSON.parse(result.content[0].text);
  console.log(`decision=${data.decision}  rule=${data.rule ?? data.why}`);
  console.log(JSON.stringify(data, null, 2));
}

await client.close();
