---
name: setup-events-daily
description: One-time setup for the events-daily project — connects Airtable and Gmail, provisions the Airtable base/tables, populates the Sources table, and creates the daily routine.
---

1. Check Airtable connector access (call the Airtable MCP `list_bases`). If it fails or no base is accessible, follow `reference/airtable-connector-setup.md`, then return here.
2. Check Gmail connector access (call the Gmail MCP `list_labels`). If it fails or no access, follow `reference/gmail-connector-setup.md`, then return here.
3. Check whether the `events-daily` Airtable base already has `Sources`/`EventLog` tables (list bases/tables via the Airtable connector). If not, run `make setup-airtable` — read the idempotency caveat in `reference/airtable-connector-setup.md` first.
4. Populate the `Sources` table — follow `reference/populate-sources-table.md`.
5. Create the Claude Code routine — follow `reference/create-routine.md`.
6. Report a final summary to the user: connectors confirmed, tables created/found, source row count, routine ID/link.

## Reference Files
- **`reference/airtable-connector-setup.md`** — connecting Airtable and running `make setup-airtable`, with the idempotency caveat.
- **`reference/gmail-connector-setup.md`** — connecting Gmail with send scope.
- **`reference/populate-sources-table.md`** — collecting the user's org/URL list and writing it to the `Sources` table.
- **`reference/create-routine.md`** — the GitHub App prerequisite and the exact `RemoteTrigger` call to create the daily routine.
