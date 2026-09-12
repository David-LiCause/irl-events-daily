# Airtable connector setup

There are **two separate Airtable credentials** in this project — don't conflate them:
1. The **Airtable OAuth connector** — used by this live session/routine to read/write `Sources`/`EventLog` records via MCP tool calls.
2. An **Airtable Personal Access Token (PAT)** — used only by the local `scripts/setup_airtable.py` script to provision the base/tables via Airtable's REST API.

## Requires the user — manual, cannot be done by Claude Code
Claude Code cannot complete either of these on the user's behalf; both open an authorization/token-creation flow only the user can approve.

- **OAuth connector:** go to claude.ai/customize/connectors → connect **Airtable** → in the authorization window that opens, log in and approve access, then select (or create) the base to scope it to.
- **PAT:** go to airtable.com/create/tokens → create a token with `data.records:read`, `data.records:write`, `schema.bases:write` scopes, and note the target workspace ID. Getting these values into `.env` is handled by `reference/env-setup.md`, not here.

**Print these two steps to the user verbatim and wait for confirmation before continuing** — do not attempt to click through, script, or otherwise bypass either flow.

## What Claude Code can do on its own, once the above is done
- **Verify the OAuth connector is connected:** call the Airtable MCP `list_bases`. An error or empty result means it isn't connected yet — stop and re-surface the manual step above rather than guessing.
- **Provision the base/tables:** run `make setup-airtable` (reads the PAT from `.env` — see `reference/env-setup.md` — calls the Airtable REST API directly, no further manual steps).
- Everything after that — reading/writing `Sources`/`EventLog` rows — is fully automatic via the OAuth connector.

## Idempotency caveat
`scripts/setup_airtable.py` always creates a *new* base — it has no check for an existing `events-daily` base/tables. Before running it, check (via the Airtable connector's `list_bases`) whether a base with those tables already exists, to avoid creating duplicates.
