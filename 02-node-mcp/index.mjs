// Pink Agentic AI Payments — Node MCP client example (sandbox only, no money moves)
//
// Connects to the sandbox MCP server with an agent key, lists the available
// tools, dry-runs a payment with pink.check_policy, then calls
// pink.request_payment and prints the decision.
//
// Usage: PINK_AGENT_KEY=pk_sandbox_agent_... node index.mjs
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

const MCP_URL = 'https://agentic-sandbox.pinkwallet.com/mcp';
const agentKey = process.env.PINK_AGENT_KEY;
if (!agentKey) {
  console.error('Set PINK_AGENT_KEY to a pk_sandbox_agent_... key (see ../01-curl/quickstart.sh).');
  process.exit(1);
}

const transport = new StreamableHTTPClientTransport(new URL(MCP_URL), {
  requestInit: { headers: { Authorization: `Bearer ${agentKey}` } },
});

const client = new Client({ name: 'pink-mcp-example', version: '1.0.0' });
await client.connect(transport);

console.log('== Tools available ==');
const { tools } = await client.listTools();
console.log(tools.map((t) => t.name).join(', '));

console.log('\n== pink.check_policy (dry run, no money moves) ==');
// Night-time rule: 23:00-06:00 local asks the owner, so we pass local_hour
// explicitly to keep this example's output the same no matter when you run it.
const check = await client.callTool({
  name: 'pink.check_policy',
  arguments: {
    payee_id: 'p_sysco',
    amount: 150,
    purpose: 'Milk and syrup restock',
    local_hour: 14,
  },
});
console.log(check.content[0].text);

console.log('\n== pink.request_payment ==');
const payment = await client.callTool({
  name: 'pink.request_payment',
  arguments: {
    payee_id: 'p_sysco',
    amount: 150,
    purpose: 'Milk and syrup restock',
    local_hour: 14,
  },
});
console.log(payment.content[0].text);

await client.close();
