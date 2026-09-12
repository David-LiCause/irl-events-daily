---
name: setup-events-daily
description: One-time setup for the events-daily project — connects Airtable and Gmail, provisions the Airtable base/tables, populates the Sources table, and creates the daily routine.
---

**This is a prescriptive, step-by-step workflow.** Execute the steps below in order, one at a time — do not skip ahead, reorder, or run steps in parallel. Before moving to the next step, confirm the current one actually completed. If any step is incomplete or cannot be completed (a connector won't connect, a command fails, required info is missing), **stop immediately and flag it to the user** — do not improvise a workaround or continue past it.

1. Set up `.env` (Airtable PAT/workspace ID, and the user's own digest recipient email) — follow `reference/env-setup.md`.
2. Check Airtable connector access (call the Airtable MCP `list_bases`). If it fails or no base is accessible, this step requires the user — you cannot connect it yourself. Print the manual instructions in `reference/airtable-connector-setup.md` to the user verbatim and wait for them to confirm before re-checking and continuing.
3. Check Gmail connector access (call the Gmail MCP `list_labels`). If it fails or no access, this step requires the user — you cannot connect it yourself. Print the manual instructions in `reference/gmail-connector-setup.md` to the user verbatim and wait for them to confirm before re-checking and continuing.
4. Check whether the `events-daily` Airtable base already has `Sources`/`EventLog` tables (list bases/tables via the Airtable connector). If not, run `make setup-airtable` — read the idempotency caveat in `reference/airtable-connector-setup.md` first.
5. Populate the `Sources` table — follow `reference/populate-sources-table.md`.
6. Create the Claude Code routine — follow `reference/create-routine.md`.
7. Report a final summary to the user: connectors confirmed, tables created/found, source row count, digest recipient email, routine ID/link.

## Reference Files
- **`reference/env-setup.md`** — creating `.env` and filling in the Airtable PAT/workspace ID and digest recipient email.
- **`reference/airtable-connector-setup.md`** — connecting Airtable (OAuth connector + PAT) and running `make setup-airtable`, with the idempotency caveat.
- **`reference/gmail-connector-setup.md`** — connecting Gmail with send scope.
- **`reference/populate-sources-table.md`** — collecting the user's org/URL list and writing it to the `Sources` table.
- **`reference/create-routine.md`** — the GitHub App prerequisite and the exact `RemoteTrigger` call to create the daily routine.
