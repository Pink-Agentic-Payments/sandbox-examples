// Pink Agentic AI Payments — a tiny agent loop (sandbox only, no money moves)
//
// Simulates an agent trying to buy 3 things against the "coffee" template's
// rules: one small order that's auto-allowed, one bigger order that needs a
// human (pending), and one to a blocked payee/category. Prints one line per
// decision. Uses only the REST API (no SDK dependency) so it's easy to read.
//
// Caveat: the coffee template has a night-time rule (23:00-06:00 local ->
// ask the owner) that would turn EVEN the "allowed" case into "pending" if
// it ran at night. We pass local_hour: 14 on every call below so the three
// outcomes are deterministic no matter when you run this.
//
// Usage: PINK_AGENT_KEY=pk_sandbox_agent_... node agent-loop.mjs

const BASE = 'https://agentic-sandbox.pinkwallet.com/v1';
const agentKey = process.env.PINK_AGENT_KEY;
if (!agentKey) {
  console.error('Set PINK_AGENT_KEY to a pk_sandbox_agent_... key for an a_purch or a_inv agent.');
  process.exit(1);
}

async function pay(payload) {
  const res = await fetch(`${BASE}/payments`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${agentKey}`,
      'Content-Type': 'application/json',
      'Idempotency-Key': `agent-loop-${payload.purpose}-${Date.now()}`,
    },
    body: JSON.stringify({ local_hour: 14, ...payload }),
  });
  return res.json();
}

// 1. Small restock order to an approved supplier, under the $500 cap -> allowed.
const purchases = [
  { payee_id: 'p_sysco', amount: 80, purpose: 'Weekly syrup top-up' },
  // 2. Bigger supply order ($500-$2,000) -> needs the store manager -> pending_human.
  { payee_id: 'p_uline', amount: 900, purpose: 'Bulk cup and lid order' },
  // 3. A new "payee" whose name trips the blocked category (gift cards/crypto/cash-like) -> blocked.
  { payee_name: 'Quick Gift Cards LLC', amount: 50, purpose: 'Buy gift cards' },
];

for (const purchase of purchases) {
  const result = await pay(purchase);
  const who = purchase.payee_id ?? purchase.payee_name;
  console.log(`[${result.decision}] ${who} $${purchase.amount} — ${result.rule ?? result.why ?? ''}`);
}
