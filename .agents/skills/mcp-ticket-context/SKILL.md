---
name: mcp-ticket-context
description: Load an external ticket or work-order through mcp-call when the user names a TICKET-* id and the full spec is not in the repo. Use when the prompt mentions TICKET-, issue IDs, or says to follow an external ticket; do not guess hidden business rules.
---

# mcp-ticket-context

The workspace does not contain the ticket body. Guessing rules will fail the hidden judge.

## Procedure

1. Confirm `mcp-call` is on PATH: `mcp-call list-servers`.
2. Discover tools: `mcp-call list-tools ticket`.
3. Fetch the named ticket:

```bash
mcp-call call ticket get_ticket --args '{"ticket_id": "TICKET-1042"}'
```

Replace the id with the one in the prompt.

4. Implement **only** the rules in that ticket. Do not invent extra discounts, tax rates, or file formats.
5. If the call is policy-denied, stop using MCP and say so; do not curl the gateway.

Tool argument names and errors are documented in `references/tool-contract.md`.
