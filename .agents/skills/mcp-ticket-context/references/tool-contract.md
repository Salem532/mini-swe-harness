# ticket MCP contract

Gateway names are `{server}__{tool}` on the wire. The CLI hides that:

| CLI | Meaning |
|-----|---------|
| `mcp-call list-servers` | allowlisted servers |
| `mcp-call list-tools ticket` | JSON list of tools + input schema |
| `mcp-call call ticket get_ticket --args '{"ticket_id":"TICKET-1042"}'` | read one ticket |

`get_ticket` arguments:

```json
{"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"]}
```

`ticket_id` must match `^[A-Z]+-[0-9]+$`. Unknown ids return an error string; retry with the id from the user prompt.

Exit codes: `0` ok, `2` policy denied, `1` other error. Denied is recoverable — pick another strategy.
